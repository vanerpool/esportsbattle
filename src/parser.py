import re
import uuid
from datetime import datetime, timedelta

import pandas as pd

from esportsbattle.config import YEAR, DATA_FOLDER

TEAM_PLAYERS_PATTERN = r'[a-zA-Zа-яА-Я][0-9.a-zA-Zа-яА-Я\s]*\([0-9._а-яА-Яa-zA-Z]*\)'
RESULT_PATTERN = r'[0-9]*\:[0-9]*'


def get_result(score_1: int, score_2: int):
    if score_1 > score_2:
        return 'W'
    elif score_1 < score_2:
        return 'L'
    elif score_1 == score_2:
        return 'D'


def parse_date(line, date):
    try:
        ret_date = YEAR + ' ' + ' '.join(line.split(' ')[:3])
        ret_time = datetime.strptime(ret_date, "%Y %d %b. %H:%M").strftime('%H:%M')
        ret_date = datetime.strptime(ret_date, "%Y %d %b. %H:%M").strftime('%Y-%m-%d')
        return ret_date, ret_time, 3
    except ValueError:
        ret_date = date + ' ' + line.split(' ')[0]
        ret_time = datetime.strptime(ret_date, "%d.%m.%Y %H:%M").strftime('%H:%M')
        ret_date = datetime.strptime(ret_date, "%d.%m.%Y %H:%M").strftime('%Y-%m-%d')
        return ret_date, ret_time, 1


def parse_games(div_results_text, date_end):
    games = []

    cur_game_home = {}
    cur_game_away = {}

    game_id = str(uuid.uuid4())

    for line in div_results_text.splitlines()[1:]:
        if 'FIFA. eSports Battle.' in line:
            league = line.split('.')[2].strip()
            continue
        if len(line.split()) > 3:
            cur_game_home['game_id'] = game_id
            cur_game_away['game_id'] = game_id

            game_date, game_time, split_idx = parse_date(line, date_end)
            cur_game_home['date'] = game_date
            cur_game_away['date'] = game_date

            cur_game_home['time'] = game_time
            cur_game_away['time'] = game_time

            cur_game_home['league'] = league
            cur_game_away['league'] = league

            line_players = ' '.join(line.split(' ')[split_idx:])

            teams = re.findall(TEAM_PLAYERS_PATTERN, line_players)
            try:
                assert len(teams) == 2
            except AssertionError:
                print('wrong input line: ', line)
                cur_game_home['not_parsed'] = line_players
                cur_game_away['not_parsed'] = line_players
                continue

            team_home = teams[0].split('(')[0].strip()
            player_home = teams[0].split('(')[1].split(')')[0].strip()
            cur_game_home['team'] = team_home
            cur_game_home['player'] = player_home
            cur_game_home['place'] = 'HOME'

            team_away = teams[1].split('(')[0].strip()
            player_away = teams[1].split('(')[1].split(')')[0].strip()
            cur_game_away['team'] = team_away
            cur_game_away['player'] = player_away
            cur_game_away['place'] = 'AWAY'

            continue
        elif line.lower() == 'матч отменен':
            print('no results for game: ', cur_game_home, cur_game_away)

            # update game_id and reset game results
            cur_game_home, cur_game_away = {}, {}
            game_id = str(uuid.uuid4())
        else:
            results = re.findall(RESULT_PATTERN, line)
            try:
                assert len(results) == 3
            except AssertionError:
                print('wrong input line: ', line)
                cur_game_home['no_results'] = line
                cur_game_away['no_results'] = line
                continue

            ft_home = int(results[0].split(':')[0])
            ft_away = int(results[0].split(':')[1])

            cur_game_home['full_time'] = ft_home
            cur_game_away['full_time'] = ft_away

            fht_home = int(results[1].split(':')[0])
            fht_away = int(results[1].split(':')[1])
            cur_game_home['first_ht'] = fht_home
            cur_game_away['first_ht'] = fht_away

            sht_home = int(results[2].split(':')[0])
            sht_away = int(results[2].split(':')[1])
            cur_game_home['second_ht'] = sht_home
            cur_game_away['second_ht'] = sht_away

            cur_game_home['result_full_time'] = get_result(ft_home, ft_away)
            cur_game_away['result_full_time'] = get_result(ft_away, ft_home)
            cur_game_home['result_first_ht'] = get_result(fht_home, fht_away)
            cur_game_away['result_first_ht'] = get_result(fht_away, fht_home)
            cur_game_home['result_second_ht'] = get_result(sht_home, sht_away)
            cur_game_away['result_second_ht'] = get_result(sht_away, sht_home)

            games.append(cur_game_home)
            games.append(cur_game_away)

            # update game_id and reset_game results
            cur_game_home, cur_game_away = {}, {}
            game_id = str(uuid.uuid4())

    return games


def save_to_file(div_results_text, date_start, date_end):
    games = parse_games(div_results_text, date_end)
    games = pd.DataFrame(games)

    dt_start = datetime.strptime(date_start, '%d.%m.%Y')
    dt_end = datetime.strptime(date_end, '%d.%m.%Y')
    for dt in pd.date_range(dt_start, dt_end):
        file_dt = dt.strftime('%Y_%m_%d')
        dt = dt.strftime('%Y-%m-%d')
        fname = DATA_FOLDER + f'games_{file_dt}.csv'

        print(f'Saving to file {fname}')

        games[games['date'] == dt].to_csv(fname, index=False, header=True)
