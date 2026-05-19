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
            

if __name__ == "__main__":
    _MPC = MPC_data()

    pass



