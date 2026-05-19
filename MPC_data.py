import os
PATH = f"{os.getcwd()}/data/test2"

class scope_info:
    def __init__(self, raw_text):
        self.instrument_info = {}
        self.waveform_info = {}
        self.data_label = []
        self.data = []
        lines = raw_text.splitlines()
        data_start = False
        for line in lines:
            cols = line.split(',')
            if len(cols) == 0:
                continue
            if cols[0] == 'TIME':
                self.data_label = cols
                data_start = True
                continue
            if data_start:
                if cols[0] == '':
                    continue
                row = {}
                for i in range(len(self.data_label)):
                    key = self.data_label[i]
                    try:
                        value = float(cols[i])
                    except:
                        value = cols[i]
                    row[key] = value
                self.data.append(row)
                continue
            key = cols[0]
            if key == '':
                continue
            values = cols[1:]
            if key in ['Model', 'Firmware Version']:
                self.instrument_info[key] = values[0]
            else:
                clean_values = []
                for v in values:
                    if v != '':
                        try:
                            clean_values.append(float(v))
                        except:
                            clean_values.append(v)
                self.waveform_info[key] = clean_values

class MPC_data:
    path = PATH
    def __init__(self):
        self.datafile_list = os.listdir(self.path)
        self.all_path = [f"{self.path}/{_x}" for _x in self.datafile_list]
        self.raw_data = []
        for _path in self.all_path:
            _f = open(_path,'r')
            self.raw_data.append(scope_info(_f.read()))
            _f.close()
        return None
    def cal_R(self):
        for scope in self.raw_data:
            for row in scope.data:

                ch3 = row.get('CH3')
                ch4 = row.get('CH4')
                if ch3 == 0:
                    row['R'] = None
                else:
                    row['R'] = ch4 / ch3
        return None
    def get_pk(self):

        for scope in self.raw_data:

            scope.pk = {}

            if len(scope.data) == 0:
                continue

            # 取得所有欄位名稱
            keys = scope.data[0].keys()

            for key in keys:

                # 跳過時間
                if key == 'TIME':
                    continue

                values = []

                for row in scope.data:

                    value = row.get(key)

                    # 避免 None
                    if isinstance(value, (int, float)):
                        values.append(value)

                if len(values) == 0:
                    continue

                scope.pk[key] = {
                    'max': max(values),
                    'min': min(values)
                }

        return None
            

if __name__ == "__main__":
    _MPC = MPC_data()
    _MPC.cal_R()
    _MPC.get_pk()
    pass



