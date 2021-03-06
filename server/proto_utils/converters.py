from ..proto_gen import Cards_pb2 as ProtoCards
from ..proto_gen import Table_pb2 as ProtoTable
from ..proto_gen import Players_pb2 as ProtoPlayers
from ..proto_gen import Betting_pb2 as ProtoBetting
from ..proto_gen import TableService_pb2 as ProtoTableService

import json
from typing import Union


def create_proto_action_request(action_token: str, action_type: str, chips=None):
    action_request = ProtoBetting.BettingActionRequest(actionToken=action_token)

    if action_type == 'FOLD':
        fold = ProtoBetting.FoldRequest()
        action_request.foldAction.CopyFrom(fold)

    elif action_type == 'CHECK':
        check = ProtoBetting.CheckRequest()
        action_request.checkAction.CopyFrom(check)

    elif action_type == 'CALL':
        call = ProtoBetting.CallRequest()
        action_request.callAction.CopyFrom(call)

    elif action_type == 'BET':
        bet = ProtoBetting.BetRequest(chips=chips)
        action_request.betAction.CopyFrom(bet)

    elif action_type == 'RAISE':
        _raise = ProtoBetting.RaiseRequest(chips=chips)
        action_request.raiseAction.CopyFrom(_raise)

    return action_request


def proto_card_to_dict(proto: ProtoCards.Card) -> dict:
    result = {
        'rank': ProtoCards.Rank.Name(proto.rank),
        'suit': ProtoCards.Suit.Name(proto.suit),
        'isHidden': False
    }
    return result


def proto_hole_card_to_dict(proto: ProtoCards.HoleCard) -> dict:
    card = proto.WhichOneof('card')

    if card == 'revealedCard':
        return proto_card_to_dict(proto.revealedCard)

    else:
        return {'isHidden': True}


def proto_positions_to_dict(proto: ProtoTable.Positions) -> Union[dict, None]:
    if proto.button == -1:
        return None

    result = {
        'button': proto.button,
        'smallBlind': proto.smallBlind,
        'bigBlind': proto.bigBlind
    }
    return result


def proto_blinds_to_dict(proto: ProtoTable.Blinds) -> dict:
    result = {
        'smallBlind': proto.smallBlind,
        'bigBlind': proto.bigBlind
    }
    return result


def proto_betting_action_log_to_action_type(proto: ProtoBetting.BettingActionLog) -> Union[str, None]:
    action = proto.WhichOneof('log')

    if action == 'postAction':
        return 'POST'
    if action == 'foldAction':
        return 'FOLD'
    if action == 'checkAction':
        return 'CHECK'
    if action == 'callAction':
        return 'CALL'
    if action == 'betAction':
        return 'BET'
    if action == 'raiseAction':
        return 'RAISE'

    return None


def proto_player_to_dict(proto: ProtoPlayers.Player) -> dict:
    result = {
        'name': proto.name,
        'seat': proto.seat,
        'stack': proto.stack,
        'currentBet': proto.bet,
        'lastAction': proto_betting_action_log_to_action_type(proto.actionLog),
        'cards': [proto_hole_card_to_dict(card) for card in proto.holeCards]
    }
    return result


def proto_betting_action_option_to_dict(proto: ProtoBetting.BettingActionOption) -> dict:
    option = proto.WhichOneof('option')

    if option == 'foldOption':
        return {'actionType': 'FOLD'}
    if option == 'checkOption':
        return {'actionType': 'CHECK'}
    if option == 'callOption':
        return {'actionType': 'CALL'}
    if option == 'betOption':
        return {'actionType': 'BET', 'chips': proto.betOption.minBet}
    if option == 'raiseOption':
        return {'actionType': 'RAISE', 'chips': proto.raiseOption.minRaise}


def proto_next_action_data_to_dict(proto: ProtoTableService.NextActionData) -> Union[dict, None]:
    next_action = proto.WhichOneof('action')
    if next_action == 'noAction':
        return None

    available_action = proto.availableAction
    result = {
        'possibleActions': [proto_betting_action_option_to_dict(option) for option in available_action.actionOptions],
        'actionToken': available_action.actionToken
    }
    return result


def proto_table_to_dict(proto: ProtoTable.Table) -> dict:
    result = {
        'seatsNumber': proto.seatsNumber,
        'positions': proto_positions_to_dict(proto.positions),
        'blinds': proto_blinds_to_dict(proto.blinds),

        'players': [proto_player_to_dict(player) for player in proto.players],
        'communityCards': [proto_card_to_dict(card) for card in proto.communityCards],
        'pots': proto.pots,

        'activePlayerSeat': proto.activePlayerSeat if proto.activePlayerSeat != -1 else None,
    }

    return result


def proto_game_update_to_dict(proto: ProtoTableService.GameUpdate) -> dict:
    result = {
        'table': proto_table_to_dict(proto.table),
    }

    next_action_data = proto_next_action_data_to_dict(proto.nextAction)
    if next_action_data is not None:
        result['actionToken'] = next_action_data['actionToken']
        result['possibleActions'] = next_action_data['possibleActions']

    return result


def proto_request_status_to_dict(proto: ProtoTableService.RequestStatus) -> dict:
    if proto.code == ProtoTableService.OK:
        code = 'OK'
        message = None

    # todo: handle other error types
    else:
        code = 'UNKNOWN_ERROR'
        message = proto.message

    return {
        'code': code,
        'message': message
    }


def proto_add_player_request_status_to_dict(proto: ProtoTableService.AddPlayerRequestStatus) -> dict:
    status_dict = proto_request_status_to_dict(proto.status)
    return {
        'code': status_dict['code'],
        'message': status_dict['message'],
        'playerToken': proto.playerToken if proto.playerToken != "" else None
    }


def table_settings_dict_to_proto(settings: dict) -> ProtoTableService.TableSettings:
    settings_string = json.dumps(settings)
    return ProtoTableService.TableSettings(jsonSettings=settings_string)


def player_token_to_proto_subscription_request(token: str) -> ProtoTableService.SubscriptionRequest:
    return ProtoTableService.SubscriptionRequest(playerToken=token)
