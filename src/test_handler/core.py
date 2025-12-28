# core.py
import pandas as pd
import matplotlib.pyplot as plt
import os
import pypdf
import pymupdf #PyMuPDF
from PIL import Image

class Importer:
    def __init__(self) -> None:
        self.path_steuerdatei = self._path_dialog_steuerdatei()
        self.path_fahne = self._path_dialog_fahne()
        self.path_to_save = self._path_to_save_dialog()
        self.path_tmp = os.path.join(self.path_to_save, 'tmp')
        self.path_output = os.path.join(self.path_to_save, 'output')

        os.mkdirs(self.path_tmp, exist_ok=True)
        os.mkdris(self.path_output, exist_ok=True)

        self.df = pd.read_csv(self.path_steuerdatei, 
                              sep=';',
                              encoding='utf-8')
        self.df = self._df_cleaner()
        self.doc = pymupdf.open(self.path_fahne)
        
        
    def _path_dialog_steuerdatei(self, 
                                 path: str ='./data/steuerung.csv') -> str:
        path_input = input("Geben Sie den Pfad zu Ihrer Steuerdatei ein: ")

        if path_input == "":
            path_input = path

        return path_input

    def _path_dialog_fahne(self, path: str = './data/fahne.pdf') -> str:
        path_input = input("Geben Sie den Pfad zu Ihrer Korrekturfahne ein: ")

        if path_input == "":
            path_input = path

        return path_input

    def _path_to_save_dialog(self, path: str = './data/tmp/') -> str:
        path_input = input('Geben Sie den Pfad zum gewünschten Speicherort ein: ')

        if path_input == "":
            path_to_save = path

        return path_to_save

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

    def main(self):
        return self.df


class StampCreator:
    def __init__(self, name: str, df) -> None:
        self.name = name
        self.df   = df

    def boxplot(self):
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
                   patch_artist=True)
        bplot['boxes'][0].set_facecolor(box_color)
        bplot['boxes'][0].set_alpha(0.6)

        val_total = self.df.loc[name, 'Total']
        val_note  = self.df.loc[name, 'Note']

        cell_text = [
            ['Punkte', f"{val_total}"],
            ['Note',   f"{val_note}"]
        ]

        table = ax.table(
        cellText=cell_text,
        loc='upper center',
        cellLoc='left',  # Text innerhalb der Zellen zentrieren
        colWidths=[0.2, 0.2] # Breite der Spalten (optional anpassbar)
        )
        
        for cell in table.get_celld().values():
            cell.set_linewidth(0)
        # 3. Styling der Tabelle
        table.scale(1, 2)       # Skaliert die Höhe der Zeilen (damit es luftiger wirkt)
        table.set_fontsize(12)

        individuelle_note = self.df.loc[name, 'Note']
    
        ax.scatter(
            x=individuelle_note, 
            y=1,              # Position auf der Y-Achse
            color='blue',      # Auffällige Farbe
            marker='o',
            s=100,            # Größe (Size) des Punktes
            zorder=3,         # WICHTIG: 3 sorgt dafür, dass der Punkt VOR der Box liegt
        )

        ax.set_yticks([])
        ax.set_xlabel('Note')
        ax.set_title(f'Individuelle Note von {self.df.loc[name, 'Vorname']} und Notenverteilung')

        fig.savefig('./data/tmp/stamp.png')

        return fig

    def stamp_remover(self) -> None:
        os.remove('./data/tmp/stamp.png')

class Stamper:
    def __init__(self, name, df):
        self.name = name
        self.df   = df
        self.file_path = self._file_path_creator()
        self.stamp = Image.open('./data/tmp/stamp.png')
        self.stamp_width, self.stamp_height = self.stamp.size
        self.doc  = self._file_importer()
        self.page_to_stamp = self._page_extractor()
        
    def _page_extractor(self):
        page = self.doc[0]
        return page

    def _file_path_creator(self, file_path=""):
        file_path = input('Geben Sie den Pfad zum Speicherort ein: ')
        clean_title = str(self.df.loc[name, 'Titel']).strip()
        clean_date  = str(self.df.loc[name, 'Datum']).strip()

        file_name   = f'{clean_date}_{name}_{clean_title}.pdf'

        if file_path == '':
            path   = os.path.join(
                             './data/tmp',
                             name,
                             file_name
                             )
        else:
            path = os.path.join(
                file_path,
                file_name
            )

        return path


    def _file_importer(self):      

        doc = pymupdf.open(self.file_path)

        return doc
        
    
    def stamp_and_save(self, position=(400, 100), max_width=200):
        """
        Stempelt die Seite unter Beibehaltung des Seitenverhältnisses
        max_width: Maximale Breite des Stempels auf dem PDF in Punkten
        """
        # Berechne Höhe basierend auf dem Seitenverhältnis
        aspect_ratio = self.stamp_height / self.stamp_width
        stamp_width = max_width
        stamp_height = max_width * aspect_ratio
        
        print(f"Original-Stempel: {self.stamp_width} x {self.stamp_height} px")
        print(f"Auf PDF: {stamp_width:.1f} x {stamp_height:.1f} Punkte")
        
        x, y = position
        img_rect = pymupdf.Rect(x, y, x + stamp_width, y + stamp_height)
        
        # Bild einfügen
        self.page_to_stamp.insert_image(img_rect, filename='./data/tmp/stamp.png')
        
        # Speichern
        self.doc.save(self.file_path, incremental=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)



    def __del__(self):
        if hasattr(self, 'doc'):
            self.doc.close()

class Resampler:
    def __init__(self, df):
        self.df = df
        self.path = './data/tmp'

    def folder_creator(self) -> None:
        
        for name in self.df.index:
            path = self.path + '/' + name

            os.mkdir(path)

    def spliter(self) -> None:
        doc = pymupdf.open('./data/fahne.pdf')
        
        for name in self.df.index:
            start_page = int(self.df.loc[name, 'First'] - 1)
            end_page   = int(self.df.loc[name, 'Last'] - 1)
            
            new_doc    = pymupdf.open()

            new_doc.insert_pdf(doc,
                               from_page=start_page, 
                               to_page=end_page)
            
            clean_title = str(self.df.loc[name, 'Titel']).strip()
            clean_date  = str(self.df.loc[name, 'Datum']).strip()

            file_name   = f'{clean_date}_{name}_{clean_title}.pdf'

            save_path   = os.path.join(
                             self.path,
                             name,
                             file_name
                             )

            new_doc.save(save_path)

            new_doc.close()





    

if __name__ == '__main__':
    # path = input('Pfad hier eingeben: ')
    test   = Importer()
    print(test.df.head())
    df = test.main()

    sampler = Resampler(df)
    sampler.folder_creator()
    sampler.spliter()

    for name in df.index:
        stamp = StampCreator(name, df)
        stamp.boxplot()
        stamp_pad = Stamper(name, df)
        stamp_pad.stamp_and_save()

    

    input('Enter drüken, um die Anzeige zu beenden.')