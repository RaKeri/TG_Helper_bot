from aiogram.fsm.state import State, StatesGroup


class Auth(StatesGroup):
    enter_filter = State()
    enter_phone = State()
    enter_code = State()
    enter_password = State()


class Grab(StatesGroup):
    enter_Proxy = State()
    waitFilter = State()
    enter_idTO = State()
    enter_id = State()
