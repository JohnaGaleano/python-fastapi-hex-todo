from typing import Iterable, Optional

from todolist.core.accounts.entities.user import UserRegistry
from todolist.core.todo.entities.todo_item import (
    CreateTodoItemDto,
    TodoItem,
    UpdateTodoItemDto,
)
from todolist.infra.database.models.todo_item import TodoItem as TodoItemModel
from todolist.infra.database.sqlalchemy import database


async def delete(user: UserRegistry, id_: int) -> bool:
    if not await exists_by_id(id_):
        return False

    query = (
        TodoItemModel.delete()
        .where(TodoItemModel.c.id == id_)
        .where(TodoItemModel.c.user_id == user.id)
    )
    await database.execute(query)
    return True


async def exists_by_id(id_: int) -> bool:
    query = TodoItemModel.count().where(TodoItemModel.c.id == id_)
    return bool(await database.execute(query))


async def fetch(user: UserRegistry, id_: int) -> Optional[TodoItem]:
    query = (
        TodoItemModel.select()
        .where(TodoItemModel.c.id == id_)
        .where(TodoItemModel.c.user_id == user.id)
    )

    result = await database.fetch_one(query)
    return TodoItem.parse_obj(dict(result)) if result else None


async def fetch_all_by_user(user: UserRegistry) -> Iterable[TodoItem]:
    query = TodoItemModel.select().where(TodoItemModel.c.user_id == user.id)

    results = await database.fetch_all(query)
    return (TodoItem.parse_obj(dict(r)) for r in results)


async def persist(user: UserRegistry, dto: CreateTodoItemDto) -> TodoItem:
    values = {**dto.dict(), "user_id": user.id}
    query = TodoItemModel.insert().values(**values)

    last_record_id = await database.execute(query)
    return TodoItem.parse_obj({**values, "id": last_record_id})


async def replace(
    user: UserRegistry, dto: CreateTodoItemDto, id_: int
) -> Optional[TodoItem]:
    if not await exists_by_id(id_):
        return None

    values = dto.dict()
    query = (
        TodoItemModel.update()
        .where(TodoItemModel.c.id == id_)
        .where(TodoItemModel.c.user_id == user.id)
        .values(**values)
    )
    await database.execute(query)
    return TodoItem.parse_obj({**values, "id": id_, "user_id": user.id})


async def update(
    user: UserRegistry, dto: UpdateTodoItemDto, id_: int
) -> Optional[TodoItem]:
    if not await exists_by_id(id_):
        return None

    values = dto.dict(exclude_unset=True)
    query = (
        TodoItemModel.update()
        .where(TodoItemModel.c.id == id_)
        .where(TodoItemModel.c.user_id == user.id)
        .values(**values)
    )
    await database.execute(query)

    return await fetch(user, id_)
