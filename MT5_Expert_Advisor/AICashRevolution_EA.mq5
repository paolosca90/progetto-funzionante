//+------------------------------------------------------------------+
//|                                          AI Cash Revolution EA   |
//|                        https://github.com/aicash-revolution      |
//|                      AI-Powered Trading Signal Execution System  |
//+------------------------------------------------------------------+
#property copyright "AI Cash Revolution Team"
#property link      "https://aicash-revolution.com"
#property version   "1.00"
#property description "Professional EA for executing AI-generated trading signals via WebSocket connection"

//--- Include necessary libraries
#include <Trade\Trade.mqh>
#include <JAson.mqh>
#include <WebSocket.mqh>

//--- Input parameters
input group "=== CONNECTION SETTINGS ==="
input string   ServerURL = "ws://localhost:9999";           // WebSocket server URL
input string   UserID = "";                                 // Your AI Cash Revolution User ID
input string   APIKey = "";                                 // Your API key
input int      ReconnectInterval = 5000;                    // Reconnection interval (ms)

input group "=== TRADING SETTINGS ==="
input double   RiskPercent = 2.0;                          // Risk per trade (% of account)
input double   MaxRiskPercent = 10.0;                      // Maximum daily risk (%)
input int      MaxOpenTrades = 5;                          // Maximum open trades
input bool     AllowBuyTrades = true;                      // Allow BUY trades
input bool     AllowSellTrades = true;                     // Allow SELL trades
input double   MaxSpread = 3.0;                            // Maximum allowed spread (pips)

input group "=== RISK MANAGEMENT ==="
input bool     UseFixedLot = false;                        // Use fixed lot size
input double   FixedLotSize = 0.01;                        // Fixed lot size (if enabled)
input double   MaxLotSize = 10.0;                          // Maximum lot size per trade
input double   MinLotSize = 0.01;                          // Minimum lot size
input bool     UseTrailingStop = true;                     // Enable trailing stop
input double   TrailingDistance = 20.0;                    // Trailing stop distance (pips)

input group "=== MONITORING ==="
input bool     EnableLogging = true;                       // Enable detailed logging
input bool     SendNotifications = true;                   // Send push notifications
input bool     ShowInfoPanel = true;                       // Show info panel on chart

//--- Global variables
CTrade         trade;
CWebSocket     websocket;
datetime       lastHeartbeat = 0;
double         dailyPnL = 0.0;
datetime       lastDailyReset = 0;
int            tradesExecutedToday = 0;
bool           isConnected = false;
string         connectionStatus = "Disconnected";

//--- Position tracking
struct SignalExecution {
   string signalId;
   ulong  ticket;
   double entryPrice;
   double stopLoss;
   double takeProfit;
   datetime openTime;
   bool   isActive;
};

SignalExecution activeSignals[];

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit() {
   //--- Validate inputs
   if(UserID == "" || APIKey == "") {
      Alert("ERROR: User ID and API Key must be configured!");
      return INIT_PARAMETERS_INCORRECT;
   }

   if(RiskPercent <= 0 || RiskPercent > 50) {
      Alert("ERROR: Risk percent must be between 0.1 and 50!");
      return INIT_PARAMETERS_INCORRECT;
   }

   //--- Initialize trading class
   trade.SetAsyncMode(false);
   trade.SetDeviationInPoints(10);
   trade.SetTypeFilling(ORDER_FILLING_FOK);

   //--- Initialize WebSocket connection
   if(!InitializeWebSocket()) {
      Print("ERROR: Failed to initialize WebSocket connection");
      return INIT_FAILED;
   }

   //--- Reset daily counters
   ResetDailyCounters();

   //--- Create info panel
   if(ShowInfoPanel) {
      CreateInfoPanel();
   }

   Print("AI Cash Revolution EA initialized successfully");
   Print("User ID: ", UserID);
   Print("Server: ", ServerURL);
   Print("Risk per trade: ", RiskPercent, "%");

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
   //--- Close WebSocket connection
   websocket.Close();

   //--- Remove info panel
   if(ShowInfoPanel) {
      RemoveInfoPanel();
   }

   Print("AI Cash Revolution EA deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() {
   //--- Check daily reset
   if(TimeToStruct(TimeCurrent()).day != TimeToStruct(lastDailyReset).day) {
      ResetDailyCounters();
   }

   //--- Check connection status
   CheckConnection();

   //--- Update trailing stops
   if(UseTrailingStop) {
      UpdateTrailingStops();
   }

   //--- Update info panel
   if(ShowInfoPanel) {
      UpdateInfoPanel();
   }

   //--- Process any pending WebSocket messages
   ProcessWebSocketMessages();
}

//+------------------------------------------------------------------+
//| Initialize WebSocket connection                                  |
//+------------------------------------------------------------------+
bool InitializeWebSocket() {
   //--- Initialize WebSocket with authentication
   string headers = "Authorization: Bearer " + APIKey + "\r\n" +
                   "User-ID: " + UserID + "\r\n" +
                   "EA-Version: 1.00\r\n";

   if(websocket.Connect(ServerURL, headers)) {
      isConnected = true;
      connectionStatus = "Connected";
      lastHeartbeat = TimeCurrent();

      //--- Send initial authentication message
      SendAuthenticationMessage();

      if(EnableLogging) {
         Print("WebSocket connected to: ", ServerURL);
      }

      return true;
   }

   connectionStatus = "Connection Failed";
   return false;
}

//+------------------------------------------------------------------+
//| Send authentication message                                      |
//+------------------------------------------------------------------+
void SendAuthenticationMessage() {
   CJAVal authMessage;
   authMessage["type"] = "auth";
   authMessage["userId"] = UserID;
   authMessage["apiKey"] = APIKey;
   authMessage["accountNumber"] = AccountInfoInteger(ACCOUNT_LOGIN);
   authMessage["accountCurrency"] = AccountInfoString(ACCOUNT_CURRENCY);
   authMessage["accountBalance"] = AccountInfoDouble(ACCOUNT_BALANCE);
   authMessage["accountEquity"] = AccountInfoDouble(ACCOUNT_EQUITY);
   authMessage["timestamp"] = (long)TimeCurrent();

   string message = authMessage.Serialize();
   websocket.Send(message);

   if(EnableLogging) {
      Print("Authentication message sent");
   }
}

//+------------------------------------------------------------------+
//| Check connection and reconnect if needed                        |
//+------------------------------------------------------------------+
void CheckConnection() {
   //--- Check if connection is alive
   if(!websocket.IsConnected()) {
      isConnected = false;
      connectionStatus = "Disconnected";

      //--- Attempt reconnection
      static datetime lastReconnectAttempt = 0;
      if(TimeCurrent() - lastReconnectAttempt > ReconnectInterval/1000) {
         if(EnableLogging) {
            Print("Attempting to reconnect...");
         }

         if(InitializeWebSocket()) {
            if(SendNotifications) {
               SendNotification("AI Cash Revolution EA reconnected");
            }
         }

         lastReconnectAttempt = TimeCurrent();
      }
   }

   //--- Send heartbeat
   if(isConnected && TimeCurrent() - lastHeartbeat > 30) {
      SendHeartbeat();
      lastHeartbeat = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| Send heartbeat message                                           |
//+------------------------------------------------------------------+
void SendHeartbeat() {
   CJAVal heartbeat;
   heartbeat["type"] = "heartbeat";
   heartbeat["timestamp"] = (long)TimeCurrent();
   heartbeat["equity"] = AccountInfoDouble(ACCOUNT_EQUITY);
   heartbeat["freeMargin"] = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   heartbeat["openTrades"] = PositionsTotal();

   string message = heartbeat.Serialize();
   websocket.Send(message);
}

//+------------------------------------------------------------------+
//| Process incoming WebSocket messages                             |
//+------------------------------------------------------------------+
void ProcessWebSocketMessages() {
   string message;
   while(websocket.ReadMessage(message)) {
      ProcessSignalMessage(message);
   }
}

//+------------------------------------------------------------------+
//| Process trading signal message                                   |
//+------------------------------------------------------------------+
void ProcessSignalMessage(string message) {
   CJAVal json;
   if(!json.Deserialize(message)) {
      if(EnableLogging) {
         Print("ERROR: Failed to parse JSON message: ", message);
      }
      return;
   }

   string messageType = json["type"].ToStr();

   if(messageType == "signal") {
      ExecuteSignal(json);
   }
   else if(messageType == "close_signal") {
      CloseSignal(json["signalId"].ToStr());
   }
   else if(messageType == "close_all") {
      CloseAllPositions();
   }
   else if(messageType == "account_info_request") {
      SendAccountInfo();
   }
   else if(messageType == "ping") {
      SendPong();
   }
}

//+------------------------------------------------------------------+
//| Execute trading signal                                           |
//+------------------------------------------------------------------+
void ExecuteSignal(CJAVal &signalData) {
   //--- Validate signal data
   if(!ValidateSignal(signalData)) {
      return;
   }

   string signalId = signalData["signalId"].ToStr();
   string symbol = signalData["symbol"].ToStr();
   string direction = signalData["direction"].ToStr();
   double entryPrice = signalData["entryPrice"].ToDbl();
   double stopLoss = signalData["stopLoss"].ToDbl();
   double takeProfit = signalData["takeProfit"].ToDbl();
   double confidence = signalData["confidence"].ToDbl();

   //--- Check if symbol is available
   if(!SymbolSelect(symbol, true)) {
      SendSignalResult(signalId, false, "Symbol not available: " + symbol);
      return;
   }

   //--- Check daily risk limit
   if(!CheckDailyRiskLimit()) {
      SendSignalResult(signalId, false, "Daily risk limit exceeded");
      return;
   }

   //--- Check maximum open trades
   if(PositionsTotal() >= MaxOpenTrades) {
      SendSignalResult(signalId, false, "Maximum open trades limit reached");
      return;
   }

   //--- Check spread
   double spread = SymbolInfoDouble(symbol, SYMBOL_SPREAD) * SymbolInfoDouble(symbol, SYMBOL_POINT);
   double maxSpreadValue = MaxSpread * SymbolInfoDouble(symbol, SYMBOL_POINT) * 10;

   if(spread > maxSpreadValue) {
      SendSignalResult(signalId, false, "Spread too high: " + DoubleToString(spread/_Point, 1) + " pips");
      return;
   }

   //--- Calculate lot size
   double lotSize = CalculateLotSize(symbol, entryPrice, stopLoss);
   if(lotSize <= 0) {
      SendSignalResult(signalId, false, "Invalid lot size calculated");
      return;
   }

   //--- Determine order type
   ENUM_ORDER_TYPE orderType;
   if(direction == "BUY") {
      if(!AllowBuyTrades) {
         SendSignalResult(signalId, false, "BUY trades are disabled");
         return;
      }
      orderType = ORDER_TYPE_BUY;
   }
   else if(direction == "SELL") {
      if(!AllowSellTrades) {
         SendSignalResult(signalId, false, "SELL trades are disabled");
         return;
      }
      orderType = ORDER_TYPE_SELL;
   }
   else {
      SendSignalResult(signalId, false, "Invalid trade direction: " + direction);
      return;
   }

   //--- Execute trade
   if(trade.PositionOpen(symbol, orderType, lotSize, 0, stopLoss, takeProfit, "AI Signal: " + signalId)) {
      ulong ticket = trade.ResultOrder();

      //--- Add to active signals tracking
      AddActiveSignal(signalId, ticket, entryPrice, stopLoss, takeProfit);

      //--- Send success result
      SendSignalResult(signalId, true, "Trade executed successfully", ticket);

      //--- Update counters
      tradesExecutedToday++;

      if(EnableLogging) {
         Print("Signal executed: ", signalId, " | ", symbol, " | ", direction, " | Lot: ", lotSize, " | Ticket: ", ticket);
      }

      if(SendNotifications) {
         SendNotification("Trade opened: " + symbol + " " + direction + " " + DoubleToString(lotSize, 2));
      }
   }
   else {
      string error = "Failed to open position: " + IntegerToString(trade.ResultRetcode());
      SendSignalResult(signalId, false, error);

      if(EnableLogging) {
         Print("ERROR: ", error, " | Signal: ", signalId);
      }
   }
}

//+------------------------------------------------------------------+
//| Validate signal data                                             |
//+------------------------------------------------------------------+
bool ValidateSignal(CJAVal &signalData) {
   //--- Check required fields
   if(!signalData.HasKey("signalId") || !signalData.HasKey("symbol") ||
      !signalData.HasKey("direction") || !signalData.HasKey("entryPrice") ||
      !signalData.HasKey("stopLoss") || !signalData.HasKey("takeProfit")) {
      if(EnableLogging) {
         Print("ERROR: Signal missing required fields");
      }
      return false;
   }

   //--- Validate numeric values
   if(signalData["entryPrice"].ToDbl() <= 0 || signalData["stopLoss"].ToDbl() <= 0 ||
      signalData["takeProfit"].ToDbl() <= 0) {
      if(EnableLogging) {
         Print("ERROR: Invalid signal prices");
      }
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Calculate appropriate lot size based on risk                    |
//+------------------------------------------------------------------+
double CalculateLotSize(string symbol, double entryPrice, double stopLoss) {
   if(UseFixedLot) {
      return NormalizeDouble(MathMax(MinLotSize, MathMin(MaxLotSize, FixedLotSize)), 2);
   }

   double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = accountBalance * RiskPercent / 100.0;

   double pointValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   double stopLossPoints = MathAbs(entryPrice - stopLoss) / SymbolInfoDouble(symbol, SYMBOL_POINT);

   double lotSize = riskAmount / (stopLossPoints * pointValue);

   //--- Normalize lot size
   double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

   lotSize = MathMax(minLot, MathMin(maxLot, lotSize));
   lotSize = MathMax(MinLotSize, MathMin(MaxLotSize, lotSize));
   lotSize = NormalizeDouble(lotSize / lotStep, 0) * lotStep;

   return lotSize;
}

//+------------------------------------------------------------------+
//| Check daily risk limit                                           |
//+------------------------------------------------------------------+
bool CheckDailyRiskLimit() {
   double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double maxDailyRisk = accountBalance * MaxRiskPercent / 100.0;

   //--- Calculate current daily P&L
   CalculateDailyPnL();

   return dailyPnL > -maxDailyRisk;
}

//+------------------------------------------------------------------+
//| Calculate daily P&L                                             |
//+------------------------------------------------------------------+
void CalculateDailyPnL() {
   dailyPnL = 0.0;
   datetime dayStart = StringToTime(TimeToString(TimeCurrent(), TIME_DATE));

   //--- Check closed positions
   HistorySelect(dayStart, TimeCurrent());
   int dealsTotal = HistoryDealsTotal();

   for(int i = 0; i < dealsTotal; i++) {
      ulong ticket = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(ticket, DEAL_TYPE) == DEAL_TYPE_BUY ||
         HistoryDealGetInteger(ticket, DEAL_TYPE) == DEAL_TYPE_SELL) {
         dailyPnL += HistoryDealGetDouble(ticket, DEAL_PROFIT);
      }
   }

   //--- Add open positions P&L
   for(int i = 0; i < PositionsTotal(); i++) {
      if(PositionSelectByIndex(i)) {
         dailyPnL += PositionGetDouble(POSITION_PROFIT);
      }
   }
}

//+------------------------------------------------------------------+
//| Send signal execution result                                     |
//+------------------------------------------------------------------+
void SendSignalResult(string signalId, bool success, string message, ulong ticket = 0) {
   CJAVal result;
   result["type"] = "signal_result";
   result["signalId"] = signalId;
   result["success"] = success;
   result["message"] = message;
   result["ticket"] = (long)ticket;
   result["timestamp"] = (long)TimeCurrent();

   if(success && ticket > 0) {
      result["openPrice"] = PositionGetDouble(POSITION_PRICE_OPEN);
      result["currentPrice"] = PositionGetDouble(POSITION_PRICE_CURRENT);
   }

   string resultMessage = result.Serialize();
   websocket.Send(resultMessage);
}

//+------------------------------------------------------------------+
//| Add signal to active tracking                                    |
//+------------------------------------------------------------------+
void AddActiveSignal(string signalId, ulong ticket, double entryPrice, double stopLoss, double takeProfit) {
   int size = ArraySize(activeSignals);
   ArrayResize(activeSignals, size + 1);

   activeSignals[size].signalId = signalId;
   activeSignals[size].ticket = ticket;
   activeSignals[size].entryPrice = entryPrice;
   activeSignals[size].stopLoss = stopLoss;
   activeSignals[size].takeProfit = takeProfit;
   activeSignals[size].openTime = TimeCurrent();
   activeSignals[size].isActive = true;
}

//+------------------------------------------------------------------+
//| Update trailing stops for all positions                         |
//+------------------------------------------------------------------+
void UpdateTrailingStops() {
   for(int i = 0; i < PositionsTotal(); i++) {
      if(PositionSelectByIndex(i)) {
         string symbol = PositionGetString(POSITION_SYMBOL);
         double currentPrice = PositionGetDouble(POSITION_PRICE_CURRENT);
         double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         double currentSL = PositionGetDouble(POSITION_SL);

         double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
         double trailingPoints = TrailingDistance * point;

         if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) {
            double newSL = currentPrice - trailingPoints;
            if(newSL > currentSL && newSL > openPrice) {
               trade.PositionModify(PositionGetInteger(POSITION_TICKET), newSL, PositionGetDouble(POSITION_TP));
            }
         }
         else if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL) {
            double newSL = currentPrice + trailingPoints;
            if((newSL < currentSL || currentSL == 0) && newSL < openPrice) {
               trade.PositionModify(PositionGetInteger(POSITION_TICKET), newSL, PositionGetDouble(POSITION_TP));
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Reset daily counters                                             |
//+------------------------------------------------------------------+
void ResetDailyCounters() {
   lastDailyReset = TimeCurrent();
   tradesExecutedToday = 0;
   dailyPnL = 0.0;

   if(EnableLogging) {
      Print("Daily counters reset");
   }
}

//+------------------------------------------------------------------+
//| Close specific signal position                                   |
//+------------------------------------------------------------------+
void CloseSignal(string signalId) {
   for(int i = 0; i < ArraySize(activeSignals); i++) {
      if(activeSignals[i].signalId == signalId && activeSignals[i].isActive) {
         if(trade.PositionClose(activeSignals[i].ticket)) {
            activeSignals[i].isActive = false;

            if(EnableLogging) {
               Print("Signal closed: ", signalId, " | Ticket: ", activeSignals[i].ticket);
            }
         }
         break;
      }
   }
}

//+------------------------------------------------------------------+
//| Close all positions                                              |
//+------------------------------------------------------------------+
void CloseAllPositions() {
   for(int i = PositionsTotal() - 1; i >= 0; i--) {
      if(PositionSelectByIndex(i)) {
         trade.PositionClose(PositionGetInteger(POSITION_TICKET));
      }
   }

   if(EnableLogging) {
      Print("All positions closed");
   }
}

//+------------------------------------------------------------------+
//| Send account information                                          |
//+------------------------------------------------------------------+
void SendAccountInfo() {
   CJAVal accountInfo;
   accountInfo["type"] = "account_info";
   accountInfo["balance"] = AccountInfoDouble(ACCOUNT_BALANCE);
   accountInfo["equity"] = AccountInfoDouble(ACCOUNT_EQUITY);
   accountInfo["margin"] = AccountInfoDouble(ACCOUNT_MARGIN);
   accountInfo["freeMargin"] = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   accountInfo["profit"] = AccountInfoDouble(ACCOUNT_PROFIT);
   accountInfo["currency"] = AccountInfoString(ACCOUNT_CURRENCY);
   accountInfo["leverage"] = AccountInfoInteger(ACCOUNT_LEVERAGE);
   accountInfo["openTrades"] = PositionsTotal();
   accountInfo["dailyPnL"] = dailyPnL;
   accountInfo["tradesExecutedToday"] = tradesExecutedToday;
   accountInfo["timestamp"] = (long)TimeCurrent();

   string message = accountInfo.Serialize();
   websocket.Send(message);
}

//+------------------------------------------------------------------+
//| Send pong response                                               |
//+------------------------------------------------------------------+
void SendPong() {
   CJAVal pong;
   pong["type"] = "pong";
   pong["timestamp"] = (long)TimeCurrent();

   string message = pong.Serialize();
   websocket.Send(message);
}

//+------------------------------------------------------------------+
//| Create information panel on chart                               |
//+------------------------------------------------------------------+
void CreateInfoPanel() {
   // Implementation for creating info panel on chart
   // This would create graphical objects showing EA status
}

//+------------------------------------------------------------------+
//| Update information panel                                         |
//+------------------------------------------------------------------+
void UpdateInfoPanel() {
   // Implementation for updating info panel
   // This would update the displayed information
}

//+------------------------------------------------------------------+
//| Remove information panel                                         |
//+------------------------------------------------------------------+
void RemoveInfoPanel() {
   // Implementation for removing info panel
   // This would clean up graphical objects
}