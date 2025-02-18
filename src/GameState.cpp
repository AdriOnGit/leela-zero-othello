/*
    This file is part of Leela Zero.
    Copyright (C) 2017-2019 Gian-Carlo Pascutto and contributors

    Leela Zero is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Leela Zero is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Leela Zero.  If not, see <http://www.gnu.org/licenses/>.

    Additional permission under GNU GPL version 3 section 7

    If you modify this Program, or any covered work, by linking or
    combining it with NVIDIA Corporation's libraries from the
    NVIDIA CUDA Toolkit and/or the NVIDIA CUDA Deep Neural
    Network library and/or the NVIDIA TensorRT inference library
    (or a modified version of those libraries), containing parts covered
    by the terms of the respective license agreement, the licensors of
    this Program grant you additional permission to convey the resulting
    work.
*/

#include <algorithm>
#include <array>
#include <cassert>
#include <iterator>
#include <memory>
#include <string>

#include "GameState.h"

#include "FastBoard.h"
#include "FastState.h"
#include "FullBoard.h"
#include "Network.h"
#include "UCTSearch.h"
#include "Utils.h"

// This class is an extension of the class FastState

// Initializes the game by initializing a FastState and other variables like time clock and previous states.
void GameState::init_game(const int size, const float komi) {
    FastState::init_game(size, komi);

    m_game_history.clear();
    m_game_history.emplace_back(std::make_shared<FastState>(*this));

    m_timecontrol.reset_clocks(); // Instance of TimeControl, manages time.

    m_resigned = FastBoard::EMPTY;
}

void GameState::reset_game() {
    FastState::reset_game();

    m_game_history.clear();
    m_game_history.emplace_back(std::make_shared<FastState>(*this));

    m_timecontrol.reset_clocks();

    m_resigned = FastBoard::EMPTY;
}

// Needed to traverse the past game states. It returns a boolean to check if the operation of moving forward with states was successful or not.
bool GameState::forward_move() {
    if (m_game_history.size() > m_movenum + 1) {
        m_movenum++;
        *(static_cast<FastState*>(this)) = *m_game_history[m_movenum]; // Updates the FastState part of the gamestate to the new move number state.
        return true;
    } else {
        return false;
    }
}

// Works the same as forward_move but in reverse.
bool GameState::undo_move() {
    if (m_movenum > 0) {
        m_movenum--;

        // this is not so nice, but it should work
        *(static_cast<FastState*>(this)) = *m_game_history[m_movenum];

        // This also restores hashes as they're part of state
        return true;
    } else {
        return false;
    }
}

// Returns to initial game state.
void GameState::rewind() {
    *(static_cast<FastState*>(this)) = *m_game_history[0];
    m_movenum = 0;
}

// Calls our internal play_move function.
void GameState::play_move(const int vertex) {
    play_move(get_to_move(), vertex);
}

// Calls the play_move function of ko_state.
void GameState::play_move(const int color, const int vertex) {
    if (vertex == FastBoard::RESIGN) {
        m_resigned = color;
    } else {
        FastState::play_move(color, vertex);
    }

    // cut off any leftover moves from navigating
    m_game_history.resize(m_movenum);
    m_game_history.emplace_back(std::make_shared<FastState>(*this));
}

// Parses a text to play a move.
bool GameState::play_textmove(std::string color, const std::string& vertex) {
    int who;
    transform(cbegin(color), cend(color), begin(color), tolower);
    if (color == "w" || color == "white") {
        who = FullBoard::WHITE;
    } else if (color == "b" || color == "black") {
        who = FullBoard::BLACK;
    } else {
        return false;
    }

    const auto move = board.text_to_move(vertex);
    if (move == FastBoard::NO_VERTEX
        /* || !is_move__legal(who, move)*/) {
        return false;
    }

    set_to_move(who);
    play_move(move);

    return true;
}

void GameState::stop_clock(const int color) {
    m_timecontrol.stop(color);
}

void GameState::start_clock(const int color) {
    m_timecontrol.start(color);
}

void GameState::display_state() {
    FastState::display_state();

    m_timecontrol.display_times();
}

int GameState::who_resigned() const {
    return m_resigned;
}

bool GameState::has_resigned() const {
    return m_resigned != FastBoard::EMPTY;
}

const TimeControl& GameState::get_timecontrol() const {
    return m_timecontrol;
}

void GameState::set_timecontrol(const TimeControl& timecontrol) {
    m_timecontrol = timecontrol;
}

void GameState::set_timecontrol(const int maintime, const int byotime,
                                const int byostones, const int byoperiods) {
    TimeControl timecontrol(maintime, byotime, byostones, byoperiods);

    m_timecontrol = timecontrol;
}

void GameState::adjust_time(const int color, const int time, const int stones) {
    m_timecontrol.adjust_time(color, time, stones);
}

void GameState::anchor_game_history() {
    // handicap moves don't count in game history
    m_movenum = 0;
    m_game_history.clear();
    m_game_history.emplace_back(std::make_shared<FastState>(*this));
}

// Sets up a handicap.
bool GameState::set_fixed_handicap(const int handicap) {
    if (handicap < 1 || handicap > 4) {
        return false;
    }

    int board_size = board.get_boardsize();

    if (handicap >= 1 && board.get_state(board.get_vertex(0, 0)) == FastBoard::EMPTY) {
        play_move(FastBoard::WHITE, board.get_vertex(0,0));
    }

    if (handicap >= 2 && board.get_state(board.get_vertex(0, board_size - 1)) == FastBoard::EMPTY) {
        play_move(FastBoard::WHITE, board.get_vertex(0, board_size-1));
    }

    if (handicap >= 3 && board.get_state(board.get_vertex(board_size - 1, board_size - 1)) == FastBoard::EMPTY) {
        play_move(FastBoard::WHITE, board.get_vertex(board_size-1, board_size-1));
    }

    if (handicap >= 4 && board.get_state(board.get_vertex(board_size - 1, 0))==FastBoard::EMPTY) {
        play_move(FastBoard::WHITE, board.get_vertex(board_size-1, 0));
    }

    anchor_game_history();

    set_handicap(handicap);

    return true;
}

const FullBoard& GameState::get_past_board(const int moves_ago) const {
    assert(moves_ago >= 0 && (unsigned)moves_ago <= m_movenum);
    assert(m_movenum + 1 <= m_game_history.size());
    return m_game_history[m_movenum - moves_ago]->board;
}

const std::vector<std::shared_ptr<const FastState>>&
GameState::get_game_history() const {
    return m_game_history;
}
