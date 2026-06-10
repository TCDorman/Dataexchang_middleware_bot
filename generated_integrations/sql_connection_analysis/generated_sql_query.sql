SELECT
    h.OrderID AS OrderID,
    h.CustomerName AS CustomerName,
    h.ShipToName AS ShipToName,
    h.ShipToAddress AS ShipToAddress,
    l.ItemNumber AS ItemNumber,
    l.Quantity AS Quantity,
    l.LocationCode AS LocationCode
FROM SalesOrders h
INNER JOIN SalesOrderLines l
    ON h.OrderID = l.OrderID;