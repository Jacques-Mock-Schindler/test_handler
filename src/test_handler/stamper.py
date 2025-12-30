# stamper.py

import pandas as pd
import matplotlib.pyplot as plt
import pymupdf
import io
from pathlib import Path

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
        # self.background = self._stamp_background_creator()
        self.doc = pymupdf.open(paths.doc)
        
    def _stamp_background_creator(self) -> plt.figure.Figure:
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
    
    def _create_stamp(self, name: str, fig: plt.figure.Figure) -> plt.figure.Figure:
        individuelle_note = self.df.loc[name, 'Note']
        vorname = self.df.loc[name, 'Vorname']
        ax = fig.axes[0]
        
        val_total = self.df.loc[name, 'Total']
        val_note  = self.df.loc[name, 'Note']

        cell_text = [
            ['Punkte', f"{val_total}"],
            ['Note',   f"{val_note}"]
        ]

        table = ax.table(
                cellText=cell_text,
                loc='upper center',
                cellLoc='left',
                colWidths=[0.2, 0.2]
        )
        
        for cell in table.get_celld().values():
            cell.set_linewidth(0)
        table.scale(1, 2)
        table.set_fontsize(12)
        
        ax.scatter(
            x = individuelle_note,
            y = 1,
            color='blue',
            marker='o',
            s=75,
            zorder=3,
        )
        ax.set_title(f'{vorname}s Note vor dem Hintergrund der Klassenleistung')
        
        return fig
    
    def _apply_stamp(self, page_number: int, fig: plt.figure.Figure):
        doc = self.doc
        buf = io.BytesIO()
        
        width_in, height_in = fig.get_size_inches()
        aspect_ratio = height_in / width_in
        
        stamp_width = 200 
        stamp_height = stamp_width * aspect_ratio
        
        x_start = 400
        y_start = 100
        position_rect = pymupdf.Rect(x_start, y_start, x_start + stamp_width, y_start + stamp_height)
        
        fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
        
        buf.seek(0)
        
        page = doc[page_number]
        
        page.insert_image(position_rect, stream=buf)
        
        buf.close()
        
    def printing_press(self) -> None:
        for name in self.df.index:
            fresh_fig = self._stamp_background_creator()
            stamp = self._create_stamp(name, fresh_fig)
            page_number = int(self.df.loc[name, 'First']) - 1
            self._apply_stamp(page_number, stamp)
            plt.close(stamp)
            
        self.doc.save('./data/fahne_gestempelt.pdf', garbage=4, deflate=True)
        
class FileManager:
    def __init__(self, paths: Pathfinder, df: DataHandler) -> None:
        self.path = paths.destination_folder
        self.df   = df.df
        
    def folder_creator(self) -> None:
        for name in self.df.index:
            path = Path(self.path) / name
            Path(path).mkdir(parents=True, exist_ok=True)
        
        
        

        
if __name__ == '__main__':
    paths = Pathfinder()
    data  = DataHandler(paths)
    print(data.df.head())
    stamp = Stamper(paths, data)
    
    stamp.printing_press()
    
    file_manager = FileManager(paths, data)
    file_manager.folder_creator()
    
    input('Zum Beenden des Programms ENTER drücken.')
    