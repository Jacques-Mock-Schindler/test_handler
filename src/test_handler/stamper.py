# stamper.py

import pandas as pd

class Pathfinder:
    def __init__(self):
        self.doc = self._doc_path_collector()
        self.data = self._data_path_collector()
        self.destination_folder = self._destination_folder_path_collector()

    def _path_collector(self, default: str, input_text: str) -> str:
        user_path = input(input_text)
        
        if user_path == '':
            return default
        else:
            return user_path

    
    def _data_path_collector(self) -> str:
        default = './data/steuerung.csv'
        input_text = 'Geben Sie hier den Pfad zur Notentabelle ein: '
        
        return self._path_collector(default, input_text)
        
    def _doc_path_collector(self) -> str:
        default = './data/fahne.pdf'
        input_text = 'Geben Sie hier den Pfad zur Korrekturfahne ein: '
        
        return self._path_collector(default, input_text)
        
    def _destination_folder_path_collector(self) -> str:
        default = './data/output/'
        input_text = ('Geben Sie hier den Pfad zum Speicherort der '
                      'gestempelten Dateien an (ohne Unterordner): ')
                      
        return self._path_collector(default, input_text)

class DataHandler:
    def __init__(self, paths: Pathfinder):
        self.df = self._df_fetcher(paths)
        self.df = self._df_cleaner()
        
    def _df_fetcher(self, paths: Pathfinder) -> None:
        df =pd.read_csv(paths.data,
                        sep=';',
                        encoding='utf-8')
        
        return df
        
    def _df_cleaner(self):
        df = self.df
        df = df.dropna()
        df = df.rename(columns=lambda x: x.replace('Nachname', 'Name') if x.startswith('Nach') else x)

        umlaute_map = str.maketrans({
            'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
            'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
            })
        
        df['Name'] = df['Name'].str.translate(umlaute_map)

        df = df.set_index('Name')

        return df
        
        

        
if __name__ == '__main__':
    paths = Pathfinder()
    data  = DataHandler(paths)
    print(data.df.head())
    