# Discord 音樂機器人及公主連結填刀機器人
## 簡介
這是一個由python所寫的Discord機器人，主要的功能有清理頻道、播放音樂以及公主連結填刀，除了清理頻道外，另外兩個功能可自行決定是否使用。

## 目錄
[python安裝](## python安裝)
[## Discord設定](## Discord設定)
[### 添加機器人至伺服器](### 添加機器人至伺服器)
[## 音樂機器人](## 音樂機器人)
[## 公主連結報刀機器人](## 公主連結報刀機器人)
[### Google sheet](### Google sheet)
[#### 取得成員的discord ID](#### 取得成員的discord ID)
[#### 建立每日報刀分頁](#### 建立每日報刀分頁)
[## 頻道清理](## 頻道清理)
[## 執行機器人](## 執行機器人)
[## 參考與感謝](## 參考與感謝)

## python安裝
1. 安裝[python](https://www.python.org/)，並將其添加至環境變數中
2. 下載本專案
3. 安裝需要的函式庫 ```pip install -r requirements.txt```

## Discord設定
1. 到[Discord application](https://discord.com/developers/applications)登入自己的帳號
2. 右上角新增Application
3. 有了application後選取左方bot頁面，新增Bot
4. 設定自己想要的頭像以及名稱
5. 設置後取得Bot的token
6. 到[discord_token.json](./discord_token.json)，在xxxx的部分填入Bot的token，```{
	"discord_token": "xxxxxxxx"
}```
### 添加機器人至伺服器
1. 在Application頁面的左方OAuth2下選取URL Generator，在scopes中勾選bot後會出現BOT PERMISSIONS，在BOT PERMISSIONS勾選Administrator，複製產生的連結
2. 或是到OAuth2底下的General中複製機器人CLIENT ID，將ID取代```https://discord.com/api/oauth2/authorize?client_id=xxxxxxx&permissions=8&scope=bot```中的xxxxxxx的部分
3. 透過連結邀請機器人至伺服器(邀請人需為伺服器擁有者)

## 音樂機器人
* 以[vbe0201](https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d)所提供的python音樂機器人程式碼為基礎進行延伸
* 新增與修改之功能
	- 針對歌曲進行音量自動調整，避免不同首音樂音量忽大忽小
	- 在join或歌曲播放完畢三分鐘後，沒有新的播放排程，機器人將會自動退出語音
	- 新增播放歌單功能
	- 新增播放清單的查看方式，利用表情選取頁數
	- 修正loop錯誤，參考[guac420之改寫](https://gist.github.com/guac420/bc612fd3a35cd00ddc1c221c560daa01)
	- 新增queue loop
* 主要功能有
	- ```!join```呼叫機器人
	- ```!play youtube網址```播放音樂
	- ```!play youtube歌單(需為公開)```播放音樂
	- ```!volumn <音量>```查看或設置音量
	- ```!loop```設置目前這首歌曲重複播放
	- ```!loopqueue```設置循環播放目前的歌單
	- ```!queue```查看待播歌曲
	- ```!pause```暫停播放
	- ```!resume```恢復播放
* 未完成功能
	- 機器人偵測語音頻道沒人自動跳出

## 公主連結報刀機器人
* 這是一個用來統計公主連結戰隊戰出刀次數與傷害的機器人，同時可以記錄是否閃退，主要發想來源為[擅長填表的高木同學](https://github.com/rjchien728/pc_discordbot)，在指令上參考了該作者的方式以及使用了其google sheet模板，主要的差別是本專案由python撰寫。

### Google sheet
* 本專案使用google sheet作為填表紀錄

#### Google sheet api
* 至[Google Cloud](https://console.cloud.google.com/)新增專案，位置填無機構就好
* 點選左側導覽清單，API和服務，上方有啟用API和服務，搜尋Google Sheet API
* 啟用Google Sheet API
* 接著在API和服務底下點選憑證
* 在憑證頁面上方點選建立憑證，選擇服務帳戶
* 在建立時把自己的gmail新增進去，讓其可以使用API
* 建立好後進入該服務帳戶，選擇金鑰，新增一個金鑰，並下載該金鑰之json，命名為```google_token.json```，放置於專案資料夾
* 雖然google sheet api在幾百萬次呼叫的情況下免費，但因為使用專案的關係，會需要綁定付費方式才能繼續使用，所以要記得綁定付費方式

#### Google sheet 模板
* 使用擅長填表的高木同學的[模板](https://docs.google.com/spreadsheets/d/1Q5FdugvDFv-EciEcrb-6KaTQ3GzXbU6E9mRZ1glQU2M/edit?usp=sharing)進行一點修改
* 點擊檔案->建立副本，建立自己公會的報刀表
* 完成後將Google Sheet網址複製至```input.json```中的```google_sheet_url```

#### 取得成員的discord ID
* 為了取得戰隊成員的discord ID，要先開啟discord的開發者模式
	- 進入discord設定 -> 外觀 -> 進階裡面有開發者模式，把它打開
* 回到公會的伺服器，對每一位成員案右鍵，複製ID
* 到剛剛複製好的Google Sheet中的```成員ID名稱對照表```
* 在第一欄輸入戰隊成員的名稱，在第二欄輸入剛剛複製的ID
* 所有戰隊成員都要進行這樣的步驟
* 填入所有戰隊成員的名稱後，記得將名稱複製到```template```頁面中
* 
#### 建立每日報刀分頁
* 機器人會自動根據日期填入報刀資訊，所以須先建立好對應日期的分頁
* 可以手動進行複製，在```template```分頁上按右鍵->複製，將新複製出來的分頁改名為戰隊戰日期，目前戰隊戰為期5天，因此要複製五次
	- 注意，因為機器人語法的緣故，日期月份的部分需要補0，假設是1月31號，分頁名稱需為```01/31```
* 或是可以使用指令```!create_sheet```，讓機器人自動創建該月份的分頁

## 頻道清理
* 為了避免誤刪訊息，需要至```input.json```中的```clear_channel```輸入想要清理的頻道名稱
* 設置後執行機器人即可使用```/clear```清理頻道訊息

## 執行機器人
* 開啟cmd，在黑框框中輸入```python base_bot.py```來執行機器人
* 如果不想要音樂機器人的功能，輸入```python base_bot.py --no-musicbot```
* 如果不想要報刀機器人的功能，輸入```python base_bot.py --no-pcbot```
* 只想要頻道清理的功能```python base_bot.py --no-musicbot --no-pcbot```

## 參考與感謝
* [擅長填表的高木同學](https://github.com/rjchien728/pc_discordbot)的報刀機器人以及google sheet模板
* [vbe0201](https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d)之音樂機器人
* [guac420](https://gist.github.com/guac420/bc612fd3a35cd00ddc1c221c560daa01)之音樂機器人loop修正