import os
import sys
import numpy as np
import pandas as pd

class VendingMachine:
  def __init__(self, id, drinks, location):
    self.id = id
    self.drinks = drinks
    self.location = location

  def simulate_sales(self, datetime, temp):
    # 初期化
    self.datetime = datetime
    self.count = dict()
    self.sales = dict()

    # 飲料ごとに売上をシミュレーション
    hour = datetime.dt.hour
    for drink in self.drinks:
      rate = drink.rate[hour] * drink.popularity

      # 温度による影響
      if drink.warm:
        rate = np.exp(np.log(rate) + 0.02*temp)
      else:
        rate = np.exp(np.log(rate) - 0.02*temp)

      # 場所による影響
      rate = rate * self.location

      # シミュレーション
      self.count[drink.id] = np.random.poisson(rate)
      self.sales[drink.id] = self.count[drink.id] * drink.price
  
  def get_sales(self):
    if self.sales is None:
      raise Exception('Please run simulate_sales() first.')
    
    dfs = list()
    for drink in self.drinks:
      df = pd.DataFrame({
        'machine_id': self.id,
        'product_id': drink.id,
        'datetime': self.datetime,
        'count': self.count[drink.id],
        'sales': self.sales[drink.id]
      })
      dfs.append(df)
      
    return pd.concat(dfs, axis=0)

class Drink:
  def __init__(self, id, price, warm, popularity):
    self.id = id                 # 飲料名
    self.price = price           # 価格 (円)
    self.warm = warm             # 種類 (温かい, 冷たい)
    self.popularity = popularity # 人気度 = 1日の売上数の期待値

    path = 'data/' + id + '.xlsx'
    df = pd.read_excel(path)
    self.rate = df['prop'].values

if __name__ == '__main__':
  root_dir = os.getcwd()
  data_dir = os.path.join(root_dir, 'data')

  # 気温データの読込
  df_temp = pd.read_csv(data_dir + '/temperature.csv')

  # 気温データの前処理
  df_temp['datetime'] = pd.to_datetime(df_temp['datetime'])
  df_temp['date'] = df_temp['datetime'].dt.date
  df_daily_temp = df_temp.groupby('date')['temperature'].median().reset_index()
  df_temp = pd.merge(df_temp, df_daily_temp, on='date', how='left', suffixes=('', '_daily'))

  # ===== ドリンクマスタの生成 =====
  df_drinks = pd.read_excel(data_dir + '/drink_specs.xlsx')
  drink_master = df_drinks[['product_id', 'product_name', 'warm', 'price']]
  drink_master.to_csv(root_dir + '/outputs/drink_master.csv', index=False)

  # ===== 自販機マスタの生成 =====
  df_vm = pd.read_excel(data_dir + '/vm_specs.xlsx')
  vm_master = df_vm[['machine_id', 'location']]
  vm_master.to_csv(root_dir + '/outputs/vm_master.csv', index=False)

  # ===== 自動販売機の売上シミュレーション =====
  # 飲料オブジェクトの初期化
  drinks = [Drink(r.product_id, r.price, r.warm, r.popularity) for r in df_drinks.itertuples()]

  # 自動販売機オブジェクトの初期化
  vms = [VendingMachine(r.machine_id, drinks, r.loc_coef) for r in df_vm.itertuples()]

  x = df_temp['datetime']
  z = df_temp['temperature_daily']

  for vm in vms:
    vm.simulate_sales(x, z)
    df_sales = vm.get_sales()
    df_sales.to_csv(root_dir + '/outputs/' + vm.id + '.csv', index=False) # 保存