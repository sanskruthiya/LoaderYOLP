import requests
import time
import sys
import csv

#ベースとなるURL
base_url = "https://map.yahooapis.jp/search/local/V1/localSearch"

api_key = input("APIキー（Client ID）を入力: ") #コマンドライン上でAPIキーの入力を求める

#都道府県コードの辞書を定義（都道府県や市区町村コードを入力しない場合、全国分を繰り返し処理で取得するため）
prefectures = {
    "01": "北海道", "02": "青森県", "03": "岩手県", "04": "宮城県", "05": "秋田県", 
    "06": "山形県", "07": "福島県", "08": "茨城県", "09": "栃木県", "10": "群馬県",
    "11": "埼玉県", "12": "千葉県", "13": "東京都", "14": "神奈川県", "15": "新潟県",
    "16": "富山県", "17": "石川県", "18": "福井県", "19": "山梨県", "20": "長野県",
    "21": "岐阜県", "22": "静岡県", "23": "愛知県", "24": "三重県", "25": "滋賀県",
    "26": "京都府", "27": "大阪府", "28": "兵庫県", "29": "奈良県", "30": "和歌山県",
    "31": "鳥取県", "32": "島根県", "33": "岡山県", "34": "広島県", "35": "山口県",
    "36": "徳島県", "37": "香川県", "38": "愛媛県", "39": "高知県", "40": "福岡県",
    "41": "佐賀県", "42": "長崎県", "43": "熊本県", "44": "大分県", "45": "宮崎県",
    "46": "鹿児島県", "47": "沖縄県"
}

#URLパラメータ用の辞書を用意し、後からパラメータを順次格納する。01はヒット総数の確認用、02はデータ取得用。
params_01 = {"appid":api_key, "results":1, "output":"json"} 
params_02 = {"appid":api_key, "output":"json"}

#パラメータを対話的に入力する
p_query = input('検索する文字列を入力（Enterキーでスキップ） >> ')
if p_query != "":
    params_01['query'] = str(p_query)
    params_02['query'] = str(p_query)
else:
    pass

p_gc = input('検索する業種コードを入力（Enterキーでスキップ） >> ')
if p_gc != "":
    params_01['gc'] = str(p_gc)
    params_02['gc'] = str(p_gc)
else:
    pass

p_ac = input('検索する都道府県または市区町村コードを入力（Enterキーでスキップ） >> ')
#都道府県コードが入力された場合
if p_ac:
    #入力されたコードが辞書にあるか確認
    if p_ac not in prefectures:
        print("無効なコードです。入力値をご確認ください。（例：北海道 => 01）")
        sys.exit()
    #有効なコードが入力されていたらパラメータに格納
    params_01['ac'] = str(p_ac)
    params_02['ac'] = str(p_ac)
else:
    pass

#ヒット件数取得用の関数
def count_data(params_01):
    response_01 = requests.get(base_url, params=params_01) #ヒット件数の確認用のリクエストを投げる処理
    jsonData_01 = response_01.json()
    return jsonData_01["ResultInfo"]["Total"]

#データ取得処理用の関数
def fetch_data(params_02, total_num, pref_name):
    max_return = 100  #APIの仕様では一回のリクエストにつき100件まで取得可能なので、その上限値を一回の取得数として設定
    pages = (int(total_num) // int(max_return)) + 1  #全件を取得するために必要なリクエスト回数を算定

    params_02['results'] = max_return  #全件取得用のパラメータを設定

    Records = []  #取得データを格納するための空リストを用意

    #全件取得するためのループ処理
    for i in range(pages):
        i_startRecord = 1 + (i * int(max_return))
        params_02['start'] = i_startRecord
        response_02 = requests.get(base_url, params=params_02)

        #レスポンスのステータスが200＝正常取得だった場合の処理
        if response_02.status_code == 200:
            try:
                jsonData_02 = response_02.json() #レスポンスをJSONデータとして格納する
            except ValueError:
                print("エラー: レスポンスデータの解析処理に失敗しました。")
                sys.exit() #ここでエラーが生じた場合は処理を終了させる。ここをcontinueに変えて、この100件分だけスキップして処理続行させることも可能。
        else:
            print("エラー:", response_02.status_code)
            sys.exit() #ここでエラーが生じた場合は処理を終了させる。

        #JSONデータ内の各発言データから必要項目を指定してリストに格納する
        for poi in jsonData_02.get('Feature', []):
            poi_id = poi.get('Id', "") #FeatureにId項目があればその値を、ない場合は空欄を返す。
            poi_name = poi.get('Name', "")
            coordinates = poi.get('Geometry', {}).get('Coordinates', "").split(",")
            poi_lat = coordinates[1] if len(coordinates) > 1 else ""
            poi_lng = coordinates[0] if len(coordinates) > 0 else ""
            Records.append([poi_id, poi_name, poi_lat, poi_lng])

        sys.stdout.write(f"\r{pref_name}: {i+1}/{pages} is done.")  #進捗状況を表示する
        sys.stdout.flush() #進捗状況を強制的に変更する
        time.sleep(0.5)  #リクエスト１回ごとに若干時間をあけてAPI側への負荷を軽減する

    #CSVへの書き出し
    csv_filename = f"poi_result_{pref_name}_{total_num}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        csvwriter = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)  #CSVの書き出し方式を適宜指定
        csvwriter.writerow(['ID', 'name', 'lat', 'lng'])
        for record in Records:
            csvwriter.writerow(record)

    print(f"\nデータ（{pref_name}）がCSV形式で出力されました。ファイル名： {csv_filename}")

#都道府県コードが入力されなかった場合、全都道府県を対象に繰り返し処理を行う
if not p_ac:
    #ヒット件数の確認用のリクエストを投げる処理
    try:
        total_num_all = count_data(params_01)
    except ValueError:
        print(f'ヒット件数取得に失敗したため、プログラムを終了します。入力パラメータをご確認ください。')
        sys.exit()
    #総ヒット件数を表示し、処理を続行するか確認
    next_input = input("検索結果は " + str(total_num_all) + "件です。\nキャンセルする場合は 1 を、データを取得するにはEnterキーまたはその他を押してください。 >> ")
    if next_input == "1":
        print(f'プログラムをキャンセルしました')
        sys.exit()
    else:
        pass

    #処理を続行する場合は、都道府県コードごとにデータ取得の繰り返し処理を実施する
    for pref_code, pref_name in prefectures.items(): #都道府県コードと名称をそれぞれ変数に格納
        params_01['ac'] = pref_code
        params_02['ac'] = pref_code

        #ヒット件数の確認用のリクエストを投げる処理
        try:
            total_num_each = count_data(params_01)
        except ValueError:
            print(f'ヒット件数取得に失敗しました。 ({pref_name})')
            continue #ここで失敗した場合、プログラム自体は終了せず、該当する都道府県の処理だけスキップ

        #ヒット件数が0件以上かつ取得条件の3100件以内だった場合は取得処理を実行、それ以外はメッセージを出して終了させる。なお、パラメータに何らかの問題があると大量のヒット件数が返されることがある。
        if total_num_each > 3100:
            print(f"データ取得上限の件数を超えているか入力パラメータが不適なため、取得処理をスキップします ({pref_name})。この都道府県では市区町村コードなどで条件を細分化してください。")
        elif total_num_each > 0:
            fetch_data(params_02, total_num_each, pref_name)
        else:
            print(f"該当するデータがありません。（{pref_name}）")

#都道府県コードが入力された場合、単一の都道府県で処理を行う
else:
    #ヒット件数の確認用のリクエストを投げる処理
    try:
        total_num = count_data(params_01)
    except ValueError:
        print(f'ヒット件数取得に失敗したため、プログラムを終了します。入力パラメータをご確認ください。')
        sys.exit()
    #総ヒット件数を表示し、処理を続行するか確認
    next_input = input("検索結果は " + str(total_num) + "件です。\nキャンセルする場合は 1 を、データを取得するにはEnterキーまたはその他を押してください。 >> ")
    if next_input == "1":
        print(f'プログラムをキャンセルしました')
        sys.exit()
    else:
        pass

    #ヒット件数が0件以上かつ取得条件の3100件以内だった場合は取得処理を実行、それ以外はメッセージを出して終了させる。なお、パラメータに何らかの問題があると大量のヒット件数が返されることがある。
    if total_num > 3100:
        print(f"データ取得上限の件数を超えているか入力パラメータが不適なため、取得処理をスキップします。市区町村コードなどで条件を細分化してください。")
    elif total_num > 0:
        fetch_data(params_02, total_num, prefectures[p_ac])
    else:
        print(f"該当するデータがありません。")
