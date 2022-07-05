MEMBER_SHEET_NAME = '成員ID名稱對照表'

LAVE = ['殘']
BOSS = ['零', '一王', '二王', '三王', '四王', '五王',]
BOSS_ONE = {'1', '1王', '一亡', '一王', '壹王', '壹', '衣王', '衣', '一'}
BOSS_TWO = {'2', '2王', '二亡', '二王', '貳王', '貳', '二'}
BOSS_THREE = {'3', '3王', '三亡', '三王', '參王', '參', '三'}
BOSS_FOUR = {'4', '4王', '四亡', '四王', '肆王', '肆', '似王', '似', '四'}
BOSS_FIVE = {'5', '5王', '五亡', '五王', '伍王', '伍', '舞王', '舞', '五'}
# abcdefghijklmnopqrstuvwxyz
# damage_colum = ['D', 'H', 'L']
DAMAGE_COLUMN = [4, 8, 12]
REHIT_DAMAGE_COLUMN = [6, 10, 14]
# boss_colum = ['E', 'I', 'M']
BOSS_COLUMN = [5, 9, 13]
REHIT_BOSS_COLUMN = [7, 11, 15]
HIT_TOP_COLUMN_NUM = 3
SLIP = 3
LAST_HIT_COLUMN_NUM = 2
TOTAL_HIT_NUM = 3
CORRECT_EMOJI = '✅'
ERROR_EMOJI = '❌'
NOT_FILL = '未填表'
IS_FILL = '已填表'
CHECK_ID = '<@(.*)>'
CHECK_REHIT = '[殘]'
REMAIN_CHANNEL = 845496409541443624
REMAIN_HOUR = 21
REMAIN_STR = '\n記得出刀喔! 出完刀別忘記填刀喔!'
music_help_str = '\
```\
!join\n呼叫機器人加入語音頻道\n\n\
!summon\n召喚機器人到目前的語音頻，機器人需已在語音頻道內\n\n\
!leave\n讓機器人離開語音頻道\n\n\
!volume <音量>\n查看或調整音量，數字需介於0~100之間\n\n\
!now\n顯示幕前撥放的歌曲\n\n\
!pause\n暫停播放\n\n\
!resume\n恢復播放\n\n\
!stop\n停止播放，playlist內的歌曲也會被刪除\n\n\
!playlist <數字>\n查看playlist內的歌曲，加上數字可跳至特定頁\n\n\
!shuffle\n打亂playlist內的歌曲順序\n\n\
!remove <數字>\n移除目前第N首歌\n\n\
!loop\n設置loop，循環撥放目前這首歌\n\n\
!loopqueue\n循環播放目前的歌單\n\n\
!play <youtube網址>\n可為歌曲或歌單\n\n\
!helpmusic\n幫助頁面\n\n\
```\
'

pc_help_str = '\
```\
!create_sheet\n呼叫機器人創建本月最後五天的報刀sheet\n\n\
!url\n呼叫機器人傳送google sheet連結\n\n\
!status\n呼叫機器人回傳目前報刀狀況\n\n\
!status @戰隊成員\n呼叫機器人回傳此成員目前報刀狀況\n\n\
!登記閃退\n登記自己閃退\n\n\
!登記閃退 @戰隊成員\n幫他人登記閃退\n\n\
!fill 傷害 boss\n報刀，依序輸入傷害以及boss目標 1~5\n\n\
!fill 傷害 boss 殘\n報殘刀，依序輸入傷害以及boss目標 1~5\n\n\
!fill @戰隊成員 傷害 boss\n幫他人報刀，標記該成員，接著輸入傷害以及boss目標 1~5\n\n\
```\
'

