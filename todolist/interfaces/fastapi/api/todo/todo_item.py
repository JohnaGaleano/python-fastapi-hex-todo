from typing import Dict, List

from fastapi import Response
from fastapi.routing import APIRouter
from toolz.itertoolz import last
from toolz.dicttoolz import assoc, dissoc, get_in
from toolz.functoolz import pipe

from todolist.domains.todo.entities.todo_item import (
    CreateTodoItemDto,
    TodoItem,
    UpdateTodoItemDto,
)
from todolist.domains.todo.services.todo_item_service import (
    create_one_todo_item,
    delete_one_todo_item,
    get_all_todo_items,
    get_one_todo_item,
    update_one_todo_item,
)


class FakeRepo:
    def __init__(self):
        self.items: Dict[int, TodoItem] = {
            1: TodoItem(id=1, msg="Item 1", is_done=False),
            2: TodoItem(id=2, msg="Item 2", is_done=False),
            3: TodoItem(id=3, msg="Item 3", is_done=False),
            4: TodoItem(id=4, msg="Item 4", is_done=True),
            5: TodoItem(id=5, msg="Item 5", is_done=True),
        }

    async def create(self, dto: CreateTodoItemDto):
        self.items, new_item = pipe(
            self.items.keys(),
            last,
            lambda key: key + 1,
            lambda new_key: TodoItem(id=new_key, msg=dto.msg, is_done=dto.is_done),
            lambda item: (assoc(self.items, item.id, item), item),
        )
        return new_item

    async def delete(self, id_):
        self.items, has_changed = pipe(
            id_,
            lambda key: dissoc(self.items, key),
            lambda new: (new, len(self.items) != len(new)),
        )
        return has_changed

    async def get_all(self):
        return list(self.items.values())

    async def get_one(self, id_):
        return get_in([id_], self.items)

    async def replace(self, dto: CreateTodoItemDto, id_: int):
        if not get_in([id_], self.items):
            return None
        self.items = assoc(
            self.items, id_, TodoItem(id=id_, msg=dto.msg, is_done=dto.is_done)
        )
        return get_in([id_], self.items)

    async def update(self, dto: UpdateTodoItemDto, id_: int):
        item = get_in([id_], self.items)
        if not item:
            return None
        self.items, new_item = pipe(
            (item, dto),
            lambda items: {**items[0].dict(), **items[1].dict(exclude_defaults=True)},
            lambda data: TodoItem(**data),
            lambda todo: (assoc(self.items, id_, todo), todo),
        )
        return new_item


fake_repo = FakeRepo()
router = APIRouter()


@router.post(
    "",
    response_model=TodoItem,
    status_code=201,
    responses={201: {"description": "Item created"}},
)
async def create(dto: CreateTodoItemDto):
    return await create_one_todo_item(fake_repo.create, dto)


@router.delete(
    "/{item_id}",
    status_code=204,
    responses={
        204: {"description": "Item deleted"},
        404: {"description": "Item not found"},
    },
)
async def delete(item_id: int):
    result = await delete_one_todo_item(fake_repo.delete, item_id)
    if not result:
        return Response(status_code=404)


@router.get(
    "",
    response_model=List[TodoItem],
    status_code=200,
    responses={200: {"description": "Items found"}},
)
async def get_all():
    return list(await get_all_todo_items(fake_repo.get_all))


@router.get(
    "/{item_id}",
    response_model=TodoItem,
    status_code=200,
    responses={
        200: {"description": "Item found"},
        404: {"description": "Item not found"},
    },
)
async def get_one(item_id: int):
    item = await get_one_todo_item(fake_repo.get_one, item_id)
    if not item:
        return Response(status_code=404)
    return item


@router.put(
    "/{item_id}",
    response_model=TodoItem,
    status_code=200,
    responses={
        200: {"description": "Item replaced"},
        404: {"description": "Item not found"},
    },
)
async def replace(dto: CreateTodoItemDto, item_id: int):
    item = await update_one_todo_item(fake_repo.replace, dto, item_id)
    return item if item else Response(status_code=404)


@router.patch(
    "/{item_id}",
    response_model=TodoItem,
    status_code=200,
    responses={
        200: {"description": "Item updated"},
        404: {"description": "Item not found"},
    },
)
async def update(dto: UpdateTodoItemDto, item_id: int):
    item = await update_one_todo_item(fake_repo.update, dto, item_id)
    return item if item else Response(status_code=404)
