# stamper.py

import pandas as pd
import matplotlib.pyplot as plt

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
    
class Stamper:
    def __init__(self, paths: Pathfinder, data: DataHandler):
        self.df = data.df
        self.background = self._stamp_background_creator()
        
    def _stamp_background_creator(self):
        # Create a figure and axis
        fig, ax = plt.subplots()

        q1 = self.df['Note'].quantile(0.25)
        q3 = self.df['Note'].quantile(0.75)

        if q1 > 4:
            box_color = 'green' 
        elif q3 < 4:
            box_color = 'red'
        else:
            box_color = 'orange'

        # Create a boxplot for the desired column
        bplot = ax.boxplot(self.df['Note'], 
                   vert=False, 
                   patch_artist=True,
                   medianprops={
                       'color': 'red',
                       'linewidth': 3,
                       'linestyle': '-',
                   })
        bplot['boxes'][0].set_facecolor(box_color)
        bplot['boxes'][0].set_alpha(0.6)
        
        ax.set_yticks([])
        ax.set_xlabel('Note')
        
        return fig
        
        

        
if __name__ == '__main__':
    paths = Pathfinder()
    data  = DataHandler(paths)
    print(data.df.head())
    stamp = Stamper(paths, data)
    
    print(stamp.background)
    stamp.background.show()
    input('Zum Beenden des Programms ENTER drücken.')
    