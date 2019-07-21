create table Users (
  UserId integer primary key,
  Name text not null,
  PIN text,
  Email text not null,
  Password text
);

create table Invoices (
  InvoiceId integer primary key,
  UserId integer not null references Users (UserId),
  IssueDate text,
  PaidDate text
);

create table ShoppingCarts (
  ShoppingCartId integer primary key,
  UserId integer not null references Users (UserId),
  InvoiceId integer references Invoices (InvoiceId)
);

create table InventoryItems (
  ItemId integer primary key,
  Name text not null,
  Barcode text,
  Price real not null
);

create table ShoppingCartItems (
  ShoppingCartItemId integer primary key,
  ShoppingCartId integer not null references ShoppingCarts (ShoppingCartId),
  ItemId integer not null references InventoryItems (ItemId)
);
