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
    noise_window = 5
    noise_zero_threshold = 2
    smooth_window = 5
    cut_tail_start_window = 5
    cut_tail_end_zero_count = 10
    def __init__(self):
        self.output_path = f"{os.getcwd()}/output"
        os.makedirs( self.output_path  ,exist_ok=True)
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
                    row['R'] = 0
                else:
                    row['R'] = ch4 / ch3
        return None
    def kill_low_noise(self):
        for scope in self.raw_data:
            if len(scope.data) < self.noise_window:
                continue

            keys = [_x for _x in scope.data[0].keys() if _x != 'TIME']

            for n in range(len(scope.data) - self.noise_window + 1):
                for key in keys:
                    values = [
                        scope.data[n + i].get(key)
                        for i in range(self.noise_window)
                    ]

                    zero_count = sum(1 for v in values if v == 0)

                    if zero_count >= self.noise_zero_threshold:
                        scope.data[n][key] = 0

        return None
    def get_pk(self):
        for scope in self.raw_data:
            scope.pk = {}
            if len(scope.data) == 0:
                continue
            keys = scope.data[0].keys()

            for key in keys:
                if key == 'TIME':
                    continue
                values = []
                for row in scope.data:
                    value = row.get(key)
                    if isinstance(value, (int, float)):
                        values.append(value)
                if len(values) == 0:
                    continue
                scope.pk[key] = {
                    'max': max(values),
                    'min': min(values)
                }
        return None
    def smooth(self):
        half = self.smooth_window // 2
        for scope in self.raw_data:
            if len(scope.data) < self.smooth_window:
                continue
            key_list = [_x for _x in scope.data[0].keys() if _x != 'TIME']
            for key in key_list:
                original = [row.get(key) for row in scope.data]
                smoothed = original[:]
                for i in range(half, len(original) - half):
                    values = original[i-half:i+half+1]
                    if not all(isinstance(v, (int, float)) for v in values):
                        continue
                    center = original[i]
                    if center == max(values):
                        continue
                    sorted_values = sorted(values)
                    smoothed[i] = sorted_values[len(sorted_values)//2]
                for i, row in enumerate(scope.data):
                    row[key] = smoothed[i]

        return None
    def write_csv(self):

        header_map = {
            'TIME': 'TIME',
            'CH1': 'Vgs',
            'CH3': 'Iout',
            'CH4': 'Vo',
            'R':'R'
        }

        for idx, scope in enumerate(self.raw_data):

            output_file = f"{self.output_path}/scope_{idx}.csv"

            lines = []

            # header
            header = [
                header_map['TIME'],
                header_map['CH1'],
                header_map['CH3'],
                header_map['CH4'],
                header_map['R']
            ]

            lines.append(','.join(header))

            # data
            for row in scope.data:

                cols = [
                    str(row.get('TIME', '')),
                    str(row.get('CH1', '')),
                    str(row.get('CH3', '')),
                    str(row.get('CH4', '')),
                    str(row.get('R', ''))
                ]

                lines.append(','.join(cols))

            _f = open(output_file, 'w')
            _f.write('\n'.join(lines))
            _f.close()

        return None
    def cut_tail(self):
        start_window = 5
        end_zero_count = 10
        keep_zero_count = end_zero_count // 2

        for scope in self.raw_data:
            data = scope.data

            if len(data) == 0:
                continue

            start_idx = 0
            end_idx = len(data)

            # 找 CH3 / CH4 peak 位置
            ch3_pk_idx = 0
            ch4_pk_idx = 0
            ch3_pk = None
            ch4_pk = None

            for i, row in enumerate(data):
                ch3 = row.get('CH3')
                ch4 = row.get('CH4')

                if isinstance(ch3, (int, float)):
                    if ch3_pk is None or ch3 > ch3_pk:
                        ch3_pk = ch3
                        ch3_pk_idx = i

                if isinstance(ch4, (int, float)):
                    if ch4_pk is None or ch4 > ch4_pk:
                        ch4_pk = ch4
                        ch4_pk_idx = i

            peak_after_idx = max(ch3_pk_idx, ch4_pk_idx)

            # 找起始點：CH1 連續 5 個點 > 0
            for i in range(len(data) - start_window + 1):
                ok = True

                for j in range(start_window):
                    ch1 = data[i + j].get('CH1')

                    if not isinstance(ch1, (int, float)) or ch1 <= 0:
                        ok = False
                        break

                if ok:
                    start_idx = i
                    break

            # 找終點：
            # 1. 必須在 CH3 peak 和 CH4 peak 之後
            # 2. CH3 連續 10 個點 = 0
            for i in range(start_idx, len(data) - end_zero_count + 1):

                if i <= peak_after_idx:
                    continue

                ok = True

                for j in range(end_zero_count):
                    ch3 = data[i + j].get('CH3')

                    if ch3 != 0:
                        ok = False
                        break

                if ok:
                    end_idx = i + keep_zero_count
                    break

            scope.data = data[start_idx:end_idx]

        return None
    def add_offset(self):
        for scope in self.raw_data:
            for row in scope.data:
                ch3 = row.get('CH3')

                if isinstance(ch3, (int, float)):
                    row['CH3'] = ch3 + 0.4

        return None

if __name__ == "__main__":
    _MPC = MPC_data()
    _MPC.add_offset()
    _MPC.kill_low_noise()
    _MPC.smooth()
    _MPC.get_pk()
    _MPC.cut_tail()
    _MPC.cal_R()
    _MPC.write_csv()
    pass



