from jpr_lib import load_config, safe_get, python_date_to_excel_number, col_name
import gspread
from datetime import datetime, timezone
import sys

DEBUG = False

def log(msg: str):
    """
    Print debug messages if DEBUG is enabled.
    """
    if DEBUG:
        print(msg)

def getFactionDonation(torn_key):
    try:
        rb = requests.get(f'https://api.torn.com/user/?selections=basic&key={torn_key}').json()
        r = requests.get(f'https://api.torn.com/faction/?selections=donations&key={torn_key}').json()
        faction_cash = r['donations'][str(rb['player_id'])]['money_balance']
        if faction_cash < 0:
            faction_cash = 0
        return faction_cash
    except KeyError as exception:
        print('Here is the KeyError :', exception)
        print('API key :', torn_key)
        return 0

def getNetworth(APIKey=''):
# STRUCTURE {"networth":{"pending":0,"wallet":300099,"bank":2270600000,"points":390267606,"cayman":0,"vault":935400000,
# "piggybank":null,"items":1072792534,"displaycase":88875999,"bazaar":7687,"properties":1087018000,
# "stockmarket":2004850585,"auctionhouse":0,"company":103827062,"bookie":null,"loan":0,"unpaidfees":0,
# "total":7953939572,"parsetime":0.06005597114562988}}
        r=requests.get(f'https://api.torn.com/user/?selections=networth&key={APIKey}').json()
        return r['networth']['total'],r['networth']['stockmarket'],r['networth']['company'],r['networth']['vault']

def getRacket(APIKey=''):
    r = requests.get(f'https://api.torn.com/v2/faction/?selections=rackets&key={APIKey}').json()
    return r["rackets"]

def racket_evolution(APIKey=''):
    # racket evolution
    ws_R = gc.open_by_key(sheetKey).worksheet('R')
    territoryNameList = []
    col = 4
    territoryName = ws_NW_data.cell(1,col).value
    while len(territoryName) == 3:
        territoryNameList.append(territoryName)
        col += 1
        territoryName = ws_NW_data.cell(1,col).value
#    territoryNameList = [ws_NW_data.acell("D1").value, ws_NW_data.acell("E1").value]
    racket_dict = getRacket(APIKey)
    for indice, territoryName in enumerate(territoryNameList):
        old_row = ws_R.cell(1, 2+indice*5).value
        old_row = int(old_row.replace(",", "").replace(" ", ""))
        current_row = old_row + 1 # row where we will eventually write new data
        if territoryName in racket_dict:
            old_level = ws_R.cell(old_row, 3+indice*5).value
            old_level = int(old_level.replace(",", "").replace(" ", ""))
            new_level = int(racket_dict[territoryName]["level"])
            old_faction_name = ws_R.cell(old_row, 5+indice*5).value
            faction_ID = racket_dict[territoryName]["faction"]
            faction_name = requests.get(
                    f"https://api.torn.com/faction/{str(faction_ID)}\
                    ?selections=&key={APIKey}").json()["name"]
            if old_level != new_level or old_faction_name != faction_name:
                # racket level or racket owner has changed
                racket_name = racket_dict[territoryName]["name"]
                reward = racket_dict[territoryName]["reward"]
                L = [[current_date_num, racket_name, new_level, reward, faction_name]]
                zone_to_be_filled = ( col_name(1+indice*5) + str(current_row) + ":"
                                    + col_name(5+indice*5) + str(current_row) )
                ws_R.update(range_name=zone_to_be_filled, values=L)
        else:
            L = [[current_date_num, "THE END :("]]
            zone_to_be_filled = ( col_name(1+indice*5) + str(current_row) + ":"
                                + col_name(2+indice*5)+ str(current_row) )
            ws_R.update(range_name=zone_to_be_filled, values=L)
    ws_R.update_cell(2,2,nodeName)
    ws_R.update_cell(3,1,current_date_num)

def get_point_value(torn_key: str, n_entry: int = 8):
    data = safe_get(f"https://api.torn.com/market/?selections=pointsmarket"
                    f"&key={torn_key}")
    points_market = data["pointsmarket"]
    costs = [entry["cost"] for entry in points_market.values()]
    # Convert dict to list of tuples (id, info) and sort by "cost"
    sorted_entries = sorted(points_market.items(),
        key=lambda item: item[1]["cost"])
    # Take first n entries with the lowest cost
    top = sorted_entries[:n_entry]
    # Compute averaged cost
    total_cost, total_quantity = 0, 0
    for id_unused, info in top:
        cost = info["cost"]
        qty = info["quantity"]
        total_cost += qty * cost
        total_quantity += qty
    averaged_cost = total_cost / total_quantity
    return averaged_cost

def main():
    config = load_config()
    json_keyfile = config["data_path"] + config["sheet_keys"]["torn_project_json"]
    spreadsheet_id = config["sheet_keys"]["torn_stats"]
    computer_name = config.get("computer", "unknown")
    gc = gspread.service_account(filename=json_keyfile)
    torn_keys = config["torn_keys"]

    # Open Tornstats sheets for NW update
    ws = gc.open_by_key(spreadsheet_id).worksheet('NW')
    ws_NW_data = gc.open_by_key(spreadsheet_id).worksheet('NW_data')

    # Current date in various format
    date_now = datetime.now(timezone.utc)
    #current_date_str = date_now.strftime("%d/%m/%Y %H:%M:%S")
    current_date_num = python_date_to_excel_number(date_now)

    # New feature, racket evolution
    # NO MORE OPERATIONNAL (changes in API v2) to be recoded.
    # racket_evolution(APIKey_dict['Kwartz'])

    # Get point value (averaged on n_entry entries)
    averaged_cost = get_point_value(torn_keys["Kwartz"], n_entry = 10)
    print(f"average point cost: {int(averaged_cost)} $")

    # Get our networth informations and combine.
    FactionDonationTotal = (getFactionDonation( torn_keys['Kivou'] ) +
                                getFactionDonation( torn_keys['Kwartz'] ) )
    NetworthKivou,StockKivou,CompanyKivou,VaultKivou = getNetworth( torn_keys['Kivou'] )
    NetworthKwartz,StockKwartz,CompanyKwartz,VaultKwartz = getNetworth( torn_keys['Kwartz'] )
    NetworthTotal = NetworthKivou + NetworthKwartz
    NetworthNet = NetworthTotal + FactionDonationTotal
    StockTotal = StockKivou + StockKwartz
    CompanyTotal = CompanyKivou + CompanyKwartz
    VaultTotal = VaultKivou + VaultKwartz
    Cash = VaultTotal + FactionDonationTotal

    ###### Add lent stocks and other investments
    # Read lent stock information from NW_Data sheet in a dictionary

    LentStocks = {}
    row = 4
    stock_id = ws_NW_data.cell(row,1).value
    while int(stock_id): # stop reading at first 0 in column "A"
        LentStocks[stock_id] = int(ws_NW_data.cell(row,2).value)
        row += 1
        stock_id = ws_NW_data.cell(row,1).value

    # Compute lent stocks value
    rs=requests.get(f'https://api.torn.com/torn/?selections=stocks&key={APIKey_dict["Kivou"]}').json()
    LentStocksTotal = 0
    for stock_id, n_increments in LentStocks.items():
        n_shares = rs["stocks"][stock_id]["benefit"]["requirement"]
        price = float(rs["stocks"][stock_id]["current_price"])
        stock_value = n_shares *  price
        LentStocksTotal += stock_value * n_increments

    RealStocks = int(StockTotal + LentStocksTotal)

    ### ADD Oil Rig/TV network Participation
    ### cell B1 CAREFUL to number format in spreadsheet
    Oil_Rig_Part = ws_NW_data.acell("B1").value
    Oil_Rig_Part = int(Oil_Rig_Part.replace(",", "").replace(" ", ""))

    ### update TV networth value
    Nub_TV_Part = ws_NW_data.acell("B2").value
    Nub_TV_Part = int(Nub_TV_Part.replace(",", "").replace(" ", ""))

    RealNetworth = int(NetworthNet + LentStocksTotal) + Oil_Rig_Part + Nub_TV_Part

    current_row = int(ws.cell(1,2).value) + 1 # row where we will write new data

    # Compute evolutions on N_average rows
    N_average = 30
    old_NW = ws.acell("H" + str(current_row - N_average)).value
    old_NW =  int(old_NW.replace(",", "").replace(" ", "")) # remove trailing and inside spaces
    old_date = ws.cell(current_row - N_average,1).value
    old_date_dt = datetime.strptime(old_date, '%d/%m/%Y %H:%M:%S') # convert to datetime

    delta_days = (datetime.now() - old_date_dt).days # use deltatime object
    Delta_averaged = int((RealNetworth  - old_NW) / delta_days)

    old_NW_1 = ws.acell("H" + str(current_row - 1)).value
    old_NW_1 = int(old_NW_1.replace(",", "").replace(" ", ""))
    Delta = int(RealNetworth  - old_NW_1)

    L = [[current_date_num, NetworthTotal, StockTotal, CompanyTotal, FactionDonationTotal, VaultTotal, RealStocks, RealNetworth, NetworthKwartz/1000000000., NetworthKivou/1000000000., Cash, Delta, Delta_averaged]]
    zone_to_be_filled = "A" + str(current_row) + ":M" + str(current_row)
    #ws.update(zone_to_be_filled, L)
    ws.update(range_name=zone_to_be_filled, values=L)
    # ws.update_cell(1,2,current_row) (now done by MATCH fonction in spreadsheet)
    ws.update_cell(2,2,nodeName)

if __name__ == "__main__":
    main()