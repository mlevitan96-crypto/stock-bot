# ALPACA CANCEL ALL ORDERS — Evidence

## Poll log (until open_orders==0, then +20s settle)

```text
cancel_all_orders() invoked at UTC 2026-03-30T20:54:37.479668+00:00
2026-03-30T20:54:37.525703+00:00Z open_orders=33
2026-03-30T20:54:42.577385+00:00Z open_orders=0
```

## Post-cancel broker truth

- Open orders: **0** (expect 0)
- Positions: **33**

### Positions

```json
[
  {
    "symbol": "AAPL",
    "side": "short",
    "qty": "-1",
    "market_value": "-246.0794",
    "avg_entry_price": "246.12",
    "qty_available": "-1",
    "asset_id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415"
  },
  {
    "symbol": "AMD",
    "side": "short",
    "qty": "-1",
    "market_value": "-195.63",
    "avg_entry_price": "193.68",
    "qty_available": "-1",
    "asset_id": "03fb07bb-5db1-4077-8dea-5d711b272625"
  },
  {
    "symbol": "BAC",
    "side": "short",
    "qty": "-4",
    "market_value": "-188.56",
    "avg_entry_price": "47.05",
    "qty_available": "-4",
    "asset_id": "061588a3-d70b-4b9c-a3f6-636aaa16acc4"
  },
  {
    "symbol": "C",
    "side": "short",
    "qty": "-2",
    "market_value": "-214.2",
    "avg_entry_price": "106.59",
    "qty_available": "-2",
    "asset_id": "36c8d04d-be51-476c-9382-0b6ea3bf1a26"
  },
  {
    "symbol": "COIN",
    "side": "short",
    "qty": "-2",
    "market_value": "-321.28",
    "avg_entry_price": "158.98",
    "qty_available": "-2",
    "asset_id": "1f3f7283-250d-4477-8b1e-037df55e5046"
  },
  {
    "symbol": "COP",
    "side": "short",
    "qty": "-2",
    "market_value": "-266.4752",
    "avg_entry_price": "132.21",
    "qty_available": "-2",
    "asset_id": "705363ac-b8c6-4d0e-9c9b-a343f3103de6"
  },
  {
    "symbol": "CVX",
    "side": "short",
    "qty": "-1",
    "market_value": "-210.9464",
    "avg_entry_price": "210.77",
    "qty_available": "-1",
    "asset_id": "186997ab-b63c-439b-bf62-72275d1c4c27"
  },
  {
    "symbol": "F",
    "side": "short",
    "qty": "-35",
    "market_value": "-391.65",
    "avg_entry_price": "11.12",
    "qty_available": "-35",
    "asset_id": "1e80b378-a5e3-4727-96bf-9c64fdd4e7e2"
  },
  {
    "symbol": "GM",
    "side": "short",
    "qty": "-2",
    "market_value": "-145.52",
    "avg_entry_price": "72.52",
    "qty_available": "-2",
    "asset_id": "de5fc535-1cdd-4a57-92ba-ac58a43aed81"
  },
  {
    "symbol": "GOOGL",
    "side": "short",
    "qty": "-1",
    "market_value": "-273.35",
    "avg_entry_price": "272.52",
    "qty_available": "-1",
    "asset_id": "69b15845-7c63-4586-b274-1cfdfe9df3d8"
  },
  {
    "symbol": "HOOD",
    "side": "short",
    "qty": "-6",
    "market_value": "-390.18",
    "avg_entry_price": "63.65",
    "qty_available": "-6",
    "asset_id": "c6e72c57-a1a9-4e4b-a7d0-029160f8bd64"
  },
  {
    "symbol": "INTC",
    "side": "short",
    "qty": "-4",
    "market_value": "-164.64",
    "avg_entry_price": "40.8",
    "qty_available": "-4",
    "asset_id": "0cf42aa3-9816-4f1f-aa84-6482ac9303e9"
  },
  {
    "symbol": "JPM",
    "side": "short",
    "qty": "-1",
    "market_value": "-283.69",
    "avg_entry_price": "282.93",
    "qty_available": "-1",
    "asset_id": "e3047683-637a-4fb2-b71d-805cd6fec95d"
  },
  {
    "symbol": "MRNA",
    "side": "short",
    "qty": "-8",
    "market_value": "-384.1392",
    "avg_entry_price": "47.29",
    "qty_available": "-8",
    "asset_id": "b02df0cc-0a0a-4ecb-8e92-201b1044ea21"
  },
  {
    "symbol": "MS",
    "side": "short",
    "qty": "-2",
    "market_value": "-316.543",
    "avg_entry_price": "157.48",
    "qty_available": "-2",
    "asset_id": "1c2f8701-b8cb-40b6-902a-1e9a6a0c7bcf"
  },
  {
    "symbol": "MSFT",
    "side": "short",
    "qty": "-1",
    "market_value": "-359",
    "avg_entry_price": "356.7",
    "qty_available": "-1",
    "asset_id": "b6d1aa75-5c9c-4353-a305-9e2caa1925ab"
  },
  {
    "symbol": "NIO",
    "side": "short",
    "qty": "-72",
    "market_value": "-398.88",
    "avg_entry_price": "5.48",
    "qty_available": "-72",
    "asset_id": "c8024b9e-d4cf-4afe-a8d9-2fa2d7ed73ac"
  },
  {
    "symbol": "NVDA",
    "side": "short",
    "qty": "-2",
    "market_value": "-330.32",
    "avg_entry_price": "164.55",
    "qty_available": "-2",
    "asset_id": "4ce9353c-66d1-46c2-898f-fce867ab0247"
  },
  {
    "symbol": "PFE",
    "side": "short",
    "qty": "-12",
    "market_value": "-332.52",
    "avg_entry_price": "27.62",
    "qty_available": "-12",
    "asset_id": "b0940983-b0c6-42f1-97d5-b1b580e4431b"
  },
  {
    "symbol": "PLTR",
    "side": "short",
    "qty": "-1",
    "market_value": "-136.85",
    "avg_entry_price": "137.1",
    "qty_available": "-1",
    "asset_id": "80e04a93-e1a8-4503-ab61-2ef1992650b4"
  },
  {
    "symbol": "RIVN",
    "side": "short",
    "qty": "-27",
    "market_value": "-388.8",
    "avg_entry_price": "14.27",
    "qty_available": "-27",
    "asset_id": "f1aaf4b2-9bc5-43ea-b56d-4341a680b775"
  },
  {
    "symbol": "SLB",
    "side": "short",
    "qty": "-4",
    "market_value": "-206.3188",
    "avg_entry_price": "51.45",
    "qty_available": "-4",
    "asset_id": "799b9c5a-54c1-4241-ba42-0dcba7d161bb"
  },
  {
    "symbol": "SOFI",
    "side": "short",
    "qty": "-26",
    "market_value": "-392.0956",
    "avg_entry_price": "14.97",
    "qty_available": "-26",
    "asset_id": "8aeca3f2-e123-4857-918b-1785a683b430"
  },
  {
    "symbol": "TGT",
    "side": "short",
    "qty": "-3",
    "market_value": "-355.5735",
    "avg_entry_price": "118.26",
    "qty_available": "-3",
    "asset_id": "b70be706-b47c-4dbd-a6a7-4e98ea48c42a"
  },
  {
    "symbol": "TSLA",
    "side": "short",
    "qty": "-1",
    "market_value": "-354.91",
    "avg_entry_price": "353.09",
    "qty_available": "-1",
    "asset_id": "8ccae427-5dd0-45b3-b5fe-7ba5e422c766"
  },
  {
    "symbol": "UNH",
    "side": "short",
    "qty": "-1",
    "market_value": "-261.5",
    "avg_entry_price": "260.53",
    "qty_available": "-1",
    "asset_id": "943bb7c3-0fb0-4088-9a37-62549b5dc528"
  },
  {
    "symbol": "WFC",
    "side": "short",
    "qty": "-2",
    "market_value": "-153.6",
    "avg_entry_price": "76.55",
    "qty_available": "-2",
    "asset_id": "f9700a20-b0fe-4516-87c5-9d7b096d5539"
  },
  {
    "symbol": "WMT",
    "side": "short",
    "qty": "-1",
    "market_value": "-123.5",
    "avg_entry_price": "123.55",
    "qty_available": "-1",
    "asset_id": "3f3e0ff9-599f-4fec-8842-6bc53f5129a1"
  },
  {
    "symbol": "XLE",
    "side": "short",
    "qty": "-6",
    "market_value": "-372.249",
    "avg_entry_price": "61.94",
    "qty_available": "-6",
    "asset_id": "2dda3c96-2138-4313-b15b-dd870c7e0ea8"
  },
  {
    "symbol": "XLF",
    "side": "long",
    "qty": "12",
    "market_value": "580.56",
    "avg_entry_price": "48.23",
    "qty_available": "12",
    "asset_id": "3b86c9e5-335d-450d-bb2b-ee4a1a658aa3"
  },
  {
    "symbol": "XLI",
    "side": "short",
    "qty": "-1",
    "market_value": "-156.61",
    "avg_entry_price": "156.36",
    "qty_available": "-1",
    "asset_id": "9f77ed09-d248-47f7-85c2-598b817fff8c"
  },
  {
    "symbol": "XLP",
    "side": "short",
    "qty": "-3",
    "market_value": "-244.74",
    "avg_entry_price": "81.82",
    "qty_available": "-3",
    "asset_id": "7e84384a-a567-4146-a496-179b29950efc"
  },
  {
    "symbol": "XOM",
    "side": "short",
    "qty": "-1",
    "market_value": "-171.81",
    "avg_entry_price": "171.82",
    "qty_available": "-1",
    "asset_id": "092efc51-b66b-4355-8132-d9c3796b9a76"
  }
]
```

### Open orders

```json
[]
```
