# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: pokerbot.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0epokerbot.proto\x12\x05poker\x1a\x1bgoogle/protobuf/empty.proto\")\n\x11ReadyCheckRequest\x12\x14\n\x0cplayer_names\x18\x01 \x03(\t\"#\n\x12ReadyCheckResponse\x12\r\n\x05ready\x18\x01 \x01(\x08\";\n\x06\x41\x63tion\x12!\n\x06\x61\x63tion\x18\x01 \x01(\x0e\x32\x11.poker.ActionType\x12\x0e\n\x06\x61mount\x18\x02 \x01(\x05\"q\n\rActionRequest\x12\x12\n\ngame_clock\x18\x01 \x01(\x02\x12\x13\n\x0bplayer_hand\x18\x02 \x03(\t\x12\x13\n\x0b\x62oard_cards\x18\x03 \x03(\t\x12\"\n\x0bnew_actions\x18\x04 \x03(\x0b\x32\r.poker.Action\"/\n\x0e\x41\x63tionResponse\x12\x1d\n\x06\x61\x63tion\x18\x01 \x01(\x0b\x32\r.poker.Action\"r\n\x0f\x45ndRoundMessage\x12\x15\n\ropponent_hand\x18\x01 \x03(\t\x12\"\n\x0bnew_actions\x18\x02 \x03(\x0b\x32\r.poker.Action\x12\r\n\x05\x64\x65lta\x18\x03 \x01(\x05\x12\x15\n\ris_match_over\x18\x04 \x01(\x08*6\n\nActionType\x12\x08\n\x04\x46OLD\x10\x00\x12\x08\n\x04\x43\x41LL\x10\x01\x12\t\n\x05\x43HECK\x10\x02\x12\t\n\x05RAISE\x10\x03\x32\xc7\x01\n\x08PokerBot\x12\x41\n\nReadyCheck\x12\x18.poker.ReadyCheckRequest\x1a\x19.poker.ReadyCheckResponse\x12<\n\rRequestAction\x12\x14.poker.ActionRequest\x1a\x15.poker.ActionResponse\x12:\n\x08\x45ndRound\x12\x16.poker.EndRoundMessage\x1a\x16.google.protobuf.Emptyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'pokerbot_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_ACTIONTYPE']._serialized_start=475
  _globals['_ACTIONTYPE']._serialized_end=529
  _globals['_READYCHECKREQUEST']._serialized_start=54
  _globals['_READYCHECKREQUEST']._serialized_end=95
  _globals['_READYCHECKRESPONSE']._serialized_start=97
  _globals['_READYCHECKRESPONSE']._serialized_end=132
  _globals['_ACTION']._serialized_start=134
  _globals['_ACTION']._serialized_end=193
  _globals['_ACTIONREQUEST']._serialized_start=195
  _globals['_ACTIONREQUEST']._serialized_end=308
  _globals['_ACTIONRESPONSE']._serialized_start=310
  _globals['_ACTIONRESPONSE']._serialized_end=357
  _globals['_ENDROUNDMESSAGE']._serialized_start=359
  _globals['_ENDROUNDMESSAGE']._serialized_end=473
  _globals['_POKERBOT']._serialized_start=532
  _globals['_POKERBOT']._serialized_end=731
# @@protoc_insertion_point(module_scope)
