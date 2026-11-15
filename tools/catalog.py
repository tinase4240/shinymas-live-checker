"""シャニマスの公式音源の曲名一覧（配信サービスの曲リスト由来）。

ライブで披露済みかどうかに関わらず「全曲」の範囲を決める。ここにあって lives.json のどの公演にもない曲は
「未披露」として data/songs.json の unperformed に出力される（build_lives.py）。

- 表記はリストのまま（"-28 colors-" や "(2023 Ver.)" などの版違いは build_lives.py が同じ曲として畳む）
- 次の4件はYouTube等の投稿で公式音源ではないため入れていない
  【シャニマス】絶対正義 EVERY DAY / 【MV MAD】デビ太郎のうた【シャニマス】 /
  想像のつばさ 樱木真乃 / 【デュエプレ×シャニマス】放っておかないファイヴァーズ
- 新曲が出たらここに足して `python3 tools/build_lives.py` を実行する
"""

CATALOG = """
Spread the Wings!! -28 colors-
Multicolored Sky -28 colors-
SNOW FLAKES MEMORIES -28 colors-
Let's get a chance -28 colors-
Ambitious Eve -28 colors-
いつか Shiny Days -28 colors-
FUTURITY SMILE -28 colors-
SWEET♡STEP -28 colors-
シャイノグラフィ -28 colors-
Dye the sky. -28 colors-
Resonance⁺ -28 colors-
Color Days -28 colors-
虹の行方 -28 colors-
Daybreak Age -28 colors-
Killer×Mission
相合学舎
Secret utopIA
ヒカリのdestination
虹になれ
We can go now!
トライアングル
Twinkle way
なんどでも笑おう (シャイニーカラーズVer.)
PRISISM
スマイルシンフォニア
FELICE
イルミネイトコンサート
バベルシティ・グレイス (2023 Ver.)
幻惑SILHOUETTE (2023 Ver.)
NEO THEORY FANTASY (2023 Ver.)
ラビリンス・レジスタンス (2023 Ver.)
Black Reverie (2023 Ver.)
純白トロイメライ (2023 Ver.)
abyss of conflict (2023 Ver.)
革命進化論 (2023 Ver.)
浮動性イノセンス
愚者の独白
アルストロメリア
ハピリリ
Bloomy!
Love Addiction
ダブル・イフェクト
Anniversary
パステルカラー パスカラカラー
ラブ・ボナペティート
VERY BERRY LOVE
Give me some more...
夢咲きAfter school
太陽キッス
ビーチブレイバー
よりみちサンセット
五ツ座流星群
学祭革命夜明け前
クライマックスアイランド
拝啓タイムカプセル
一閃は君が導く
キャットスクワッド
Wandering Dream Chaser
Transcending The World
Hide & Attack
Destined Rival
Another Rampage
Timeless Shooting Star
Tracing Defender
Overdrive Emotion
いつだって僕らは
あの花のように
僕らだけの未来の空
今しかない瞬間を
Catch the Breeze
アスファルトを鳴らして
OH MY GOD
Fly and Fly
Fashionable
Bouncy Girl
無自覚アプリオリ
くだらないや
平行線の美学
青空
ハナムケのハナタバ
枕木の歌
Happier
とある英雄たちの物語
Unsung Heroes
有彩色ユリイカ
文明開花輪舞 -シティ・ハレルヤ-
秋の終わり、僕の記憶
時限式狂騒ワンダーランド
LINKs
メッセージ
Love Letter
グラデーション
裸足じゃイラレナイ
明日もBeautiful Day
ハナサカサイサイ
全力アンサー
ひめくりモザイク
Imitation Ghost
BURN BURN
Start up Stand up
Reflection
夢が夢じゃなくなるその日まで
青とオレンジ
フェアリー・ガール
Look up to the sky
Forbidden Paradise
SWEETEST BITE
White Story
GOTCHA
Forward March！！！
星が流れて
BRIGHTEST WHITE
Shiny Stories
星の声
ツバサグラビティ
GR＠TITUDE (シャイニーカラーズVer.)
VOY@GER (シャイニーカラーズVer.)
ありったけの輝きで
星をめざして
夢見鳥
アポイント・シグナル
チョコデート・サンデー
Sweet Memories
ハナマルバッジ
誰ソ彼アイデンティティー
わたしの主人公はわたしだから！
また明日
常咲の庭
プラスチック・アンブレラ (2022 Ver.)
Going my way
雪・月・風・花
スローモーション
千夜アリア
Damascus Cocktail
Darling you!
あおぞらサイダー
SOS
過純性ブリーチ
HAREBARE!!
statice
放課後マギア
パーティーマジックデザイナー
輝きにかわる
Happy Funny Lucky
アスタラブビスタ
DAYDREAM LOVE
mellow mellow
After Run
ホムラインビテーション
ONE STAR
ねぇ、ねぇ、ねぇ
OPEN the New world
Midnight parade!
CANDY UNIVERSE
Poison Berry Daughters
プリズムフレア
C'mon! Join Us
愛なView
サマーサマーオーシャンパーリィバケーション
神様は死んだ、って (2024 Remastering Ver.)
無垢
夢模様キャンバス
Cyber Parkour
LIVE LIVE LIVE!
Monochromatic
Snowflake
Heads or Tails？
グッバイ
いつかのキミへ
365日のストーリー
星の数だけ
橙より未来
さあ舞い上がれ
With you
Future Designer
未来へのSign
泥濘鳴鳴
Clean.Clean up
快盗Vを見逃すな
Shower of light
Real Mind Shakes
THE LAST PRIDE
愛しき日々
Fading Stars
Future Transit
KoiKyun！
Migratory Echoes
Pioneer Impact
ブレイク・アウト・セレンディピティ
Break Chain
リフレインブレイン
ルピラ
似セ者
迅雷鉄火
進路は超銀河
GET OVER
STARRY PLACE
晴れのちバルーン
Sparkle
REWRITING
Swing it!
乱舞る
1/3
Borderline
クローバー
Summer Night Paradise
カウントダウンラブ
KAWAII♡めたもる交響曲
QUEEN OF THE PIRATES
キラピコ.exe
Sleepless Nights
アイノウ
疾風ザブングル
Karma
Naraku
感謝のコントレイル
キズナシェアリング
Lit up my sky
永遠色アーチ
ボーダーレス・ノンストレス
Oh Yeah!!
銀翼のアレジアンス -blade of truth-
メモワール・アンタクト
運命前夜
月影のアンシェネ
Once Upon a Secret
銀翼のアヴニール -become the brave-
SUPER DUPER DREAMER
BEAST MODE
One Live One Love
Ring Ring Ringの魔法
街角メランコリー
散花-sanka-
紅花-benibana-
Tokyo自由系*ガール
My time
泡沫に染まる
MAGICAL FOREST
恋するクオリア
ハグルマヒマワリ
ナイススパイス研究会
どっちみちLOVE
ワタシグラビティ
ダミーガール
Crying Diamond
Imaginary
Embers glow
正解な不正解
最上級パンチライン
カラースプレーとうさぎさん
月とネオンと薄紅と
Odette
Hold on me
Here for you
HELL-O
Take Ur Time
Lights on me
パラボラ
Be-witched
Sweet Boozy
ガガリズム
Paradox
ハートフルデイ ハートフルミー
Unstoppable
HSV色空間
プラニスフィア ～planisphere～ -9 colors-
リフレクトサイン -9 colors-
SOLAR WAY -10 colors-
BEAM
OVERLAY OF HOPES
""".strip().splitlines()
