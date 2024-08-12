# 自販機売上データセット

## セットアップ

まず仮想環境を構築する.
```bash
python -m venv env
source env/bin/activate
```

次に必要なライブラリをインストールする.
```bash
pip install -r requirements.txt
```

## データセットの生成方法
データセットを生成するには以下のコマンドを実行する.
```bash
python generate_dataset.py
```

### 生成されたデータセット
- `drink_master.csv`: 飲み物のマスターデータ
- `vm_master.csv`: 自動販売機のマスターデータ
- `midXYZ.csv`: 自動販売機ごとの売上データ

## 生成設定
### 時系列
各ドリンクの1時間あたりの売上レートは `pidXYZ.xlsx` ファイルの `prop` 変数で決定される. 1日に販売される飲料の予想数は `drink_specs.xlsx` ファイルの `popularity` 変数で決定される. ここで, $\beta_i$ を飲み物 $i$ の人気度, $\pi_{i,h}$を時間$h$に売れた飲み物 $i$ の割合とする. すると, 1時間あたりのドリンク販売数の基本式は以下のようになる:
$$
\begin{align*}
Y_{i,h} &\sim \text{Poisson}(\lambda_{i,h}) \\
\lambda_{i,h} &= \beta_i \pi_{i,h}
\end{align*}
$$

### 長期トレンド
各ドリンクの1日の売上は気温と相関がある. 温度との関係は `drink_specs.xlsx` ファイルの `warm` 変数によって決定される. もし `warm` 変数が `TRUE` ならば, 飲み物は気温と負の相関があり, `warm` 変数が `FALSE` ならばその逆である. $T_d$ を $d$ 日の気温の中央値, $D_i$ を `warm` が `TRUE` のときに値 1, それ以外のときに値 0 をとるダミー変数とする. すると, 1日あたりの飲料販売数の基本式は以下のようになる:

$$
\begin{align*}
Y_{i,d,h} &\sim \text{Poisson}(\lambda_{i,d,h}) \\
\lambda_{i,d,h} &= \exp \left( \log(\beta_i\pi_{i,h}) + (-1)^{D_i} \times 0.02 \times T_d \right)
\end{align*}
$$

### 地域効果
各飲料の売上は自動販売機の設置場所にも影響されます。立地との関係は `vm_specs.xlsx` ファイル中の `loc_coef` 変数によって決定される。自販機 $j$ の `loc_coef` の値を $\gamma_j$ とする。すると、1日あたりの飲料販売数の計算式は以下のようになる:
$$
\begin{align*}
Y_{i,j,d,h} &\sim \text{Poisson}(\lambda_{i,j,d,h}) \\
\lambda_{i,j,d,h} &= \gamma_j\exp \left(\log(\beta_i\pi_{i,h}) + (-1)^{D_i} \times 0.02 \times T_d \right)
\end{align*}
$$