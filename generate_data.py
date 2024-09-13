import os
import sys
import numpy as np
import pandas as pd

class VendingMachine:
  def __init__(self, id, inventory, location):
    self.id = id
    self.location = location
    self.inventory = inventory # 在庫

    self.sales = {}
    for drink in inventory:
      self.sales[drink] = {'time': [], 'count': [], 'sales': []}

    self.replenish()
    
  def replenish(self):
    """在庫の補充"""
    for drink in self.inventory:
      self.inventory[drink]['stock'] = self.inventory[drink]['max']

  def sale(self, time, drink, n):
    stock = self.inventory[drink]['stock']
    if stock > 0: # 在庫があれば
      if stock > n:
        self.inventory[drink]['stock'] = stock - n
        self.sales[drink]['count'].append(n)
      else:
        self.inventory[drink]['stock'] = 0
        self.sales[drink]['count'].append(stock)

    else: # 在庫がなければ
      self.sales[drink]['count'].append(0)
    
    self.sales[drink]['time'].append(time)
  
  def get_sales(self):
    if self.sales is None:
      raise Exception('Please run simulate_sales() first.')
    
    dfs = list()
    for drink in self.inventory:
      df = pd.DataFrame({
        'machine_id': self.id,
        'product_id': drink,
        'datetime': self.sales[drink]['time'],
        'count': self.sales[drink]['count']
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

def simulate_sales(vms, drinks, datetime, temp):
  for i in range(len(datetime)):
    for vm in vms:
      for drink in drinks:
        dow = datetime[i].dayofweek
        hour = datetime[i].hour

        # 毎週月曜日の0時に在庫を補充
        if dow == 0 and hour == 0:
          vm.replenish() 
      
        rate = drink.rate[hour] * drink.popularity
        if drink.warm:
          rate = np.exp(np.log(rate) + 0.02*temp[i])
        else:
          rate = np.exp(np.log(rate) - 0.02*temp[i])

        rate = rate * vm.location
        n = np.random.poisson(rate)
        vm.sale(datetime[i], drink.id, n)

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
  inventory = {
    'pid001': {'max': 100, 'stock': 100},
    'pid002': {'max': 100, 'stock': 100},
    'pid003': {'max': 100, 'stock': 100},
  }

  vms = [VendingMachine(r.machine_id, inventory, r.loc_coef) for r in df_vm.itertuples()]

  x = df_temp['datetime']
  z = df_temp['temperature_daily']

  simulate_sales(vms, drinks, x, z)
  for vm in vms:
    df_sales = vm.get_sales()
    df_sales.to_csv(root_dir + '/outputs/' + vm.id + '.csv', index=False) # 保存