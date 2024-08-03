from fastapi import FastAPI, HTTPException

from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, SQLModel, create_engine, Session, select

class BaseWallet(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    balance: float
    


class BaseItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None
    price: float = 0.12
    tax: float | None = None


class BaseMerchant(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class BaseTransaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    amount: float
    merchant_id: int


class CreatedItem(BaseItem):
    pass


class UpdatedItem(BaseItem):
    pass


class Item(BaseItem):
    id: int

class DBWallet(BaseWallet, SQLModel,table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class DBItem(Item, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class DBMerchant(BaseMerchant, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class DBTransaction(BaseTransaction, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
class ItemList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[Item]
    page: int
    page_size: int
    size_per_page: int


connect_args = {}

engine = create_engine(
    "postgresql+pg8000://postgres:123456@localhost/digimondb",
    echo=True,
    connect_args=connect_args,
)


SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/items")
async def create_item(item: CreatedItem) -> Item:
    print("create_item", item)
    data = item.dict()
    dbitem = DBItem(**data)
    with Session(engine) as session:
        session.add(dbitem)
        session.commit()
        session.refresh(dbitem)

    # return Item.parse_obj(dbitem.dict())
    return Item.from_orm(dbitem)


@app.get("/items")
async def read_items() -> ItemList:
    with Session(engine) as session:
        items = session.exec(select(DBItem)).all()

    return ItemList.from_orm(dict(items=items, page_size=0, page=0, size_per_page=0))


@app.get("/items/{item_id}")
async def read_item(item_id: int) -> Item:
    with Session(engine) as session:
        db_item = session.get(DBItem, item_id)
        if db_item:
            return Item.from_orm(db_item)
    raise HTTPException(status_code=404, detail="Item not found")


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: UpdatedItem) -> Item:
    print("update_item", item)
    data = item.dict()
    with Session(engine) as session:
        db_item = session.get(DBItem, item_id)
        db_item.sqlmodel_update(data)
        session.add(db_item)
        session.commit()
        session.refresh(db_item)

    return Item.from_orm(db_item)


@app.delete("/items/{item_id}")
async def delete_item(item_id: int) -> dict:
    with Session(engine) as session:
        db_item = session.get(DBItem, item_id)
        session.delete(db_item)
        session.commit()

    return dict(message="delete success")


@app.post("/wallets")
async def create_wallet(wallet: BaseWallet) -> BaseWallet:
    print("create_wallet", wallet)
    data = wallet.dict()
    dbwallet = DBWallet(**data)
    with Session(engine) as session:
        session.add(dbwallet)
        session.commit()
        session.refresh(dbwallet)

    return BaseWallet.from_orm(dbwallet)


@app.get("/wallets/{wallet_id}")
async def read_wallet(wallet_id: int) -> BaseWallet:
    with Session(engine) as session:
        db_wallet = session.get(DBWallet, wallet_id)
        if db_wallet:
            return BaseWallet.from_orm(db_wallet)
    raise HTTPException(status_code=404, detail="Wallet not found")


@app.post("/merchant/")
async def create_merchant(merchant: BaseMerchant) -> BaseMerchant:
    print("create_merchant", merchant)
    data = merchant.dict()
    dbmerchant = DBMerchant(**data)
    with Session(engine) as session:
        session.add(dbmerchant)
        session.commit()
        session.refresh(dbmerchant)

    return BaseMerchant.from_orm(dbmerchant)


@app.get("/merchant/{merchant_id}")
async def read_merchant(merchant_id: int) -> BaseMerchant:
    with Session(engine) as session:
        db_merchant = session.get(DBMerchant, merchant_id)
        if db_merchant:
            return BaseMerchant.from_orm(db_merchant)
    raise HTTPException(status_code=404, detail="Merchant not found")


@app.post("/transaction/")
async def create_transaction(transaction: BaseTransaction) -> BaseTransaction:
    print("create_transaction", transaction)
    data = transaction.dict()
    dbtransaction = DBTransaction(**data)
    with Session(engine) as session:
        session.add(dbtransaction)
        session.commit()
        session.refresh(dbtransaction)

    return BaseTransaction.from_orm(dbtransaction)


@app.get("/transaction/{transaction_id}")
async def read_transaction(transaction_id: int) -> BaseTransaction:
    with Session(engine) as session:
        db_transaction = session.get(DBTransaction, transaction_id)
        if db_transaction:
            return BaseTransaction.from_orm(db_transaction)
    raise HTTPException(status_code=404, detail="Transaction not found")

