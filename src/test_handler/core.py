# core.py
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
import pymupdf  # PyMuPDF
from PIL import Image

class Importer:
    def __init__(self) -> None:
        self.path_steuerdatei = self._path_dialog_steuerdatei()
        self.path_fahne = self._path_dialog_fahne()
        self.path_to_save = self._path_to_save_dialog()
        self.path_tmp = os.path.join(self.path_to_save, 'tmp')
        self.path_output = os.path.join(self.path_to_save, 'output')

        os.makedirs(self.path_tmp, exist_ok=True)
        os.makedirs(self.path_output, exist_ok=True)

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

    def _path_to_save_dialog(self, path: str = './data/') -> str:  # ✓ KORRIGIERT
        path_input = input('Geben Sie den Pfad zum gewünschten Speicherort ein: ')

        if path_input == "":
            path_input = path  # ✓ KORRIGIERT

        return path_input  # ✓ KORRIGIERT

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
    def __init__(self, name: str, importer: Importer) -> None:
        self.name = name
        self.df   = importer.df
        self.path_tmp = importer.path_tmp

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

        val_total = self.df.loc[self.name, 'Total']  # ✓ KORRIGIERT
        val_note  = self.df.loc[self.name, 'Note']   # ✓ KORRIGIERT

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

        individuelle_note = self.df.loc[self.name, 'Note']  # ✓ KORRIGIERT
    
        ax.scatter(
            x=individuelle_note, 
            y=1,
            color='blue',
            marker='o',
            s=100,
            zorder=3,
        )

        ax.set_yticks([])
        ax.set_xlabel('Note')
        ax.set_title(f'Individuelle Note von {self.df.loc[self.name, "Vorname"]} und Notenverteilung')  # ✓ KORRIGIERT

        stamp_path = os.path.join(self.path_tmp, 'stamp.png')        
        fig.savefig(stamp_path)
        
        # ✓ WICHTIG: Figur schließen, damit die Datei freigegeben wird
        plt.close(fig)

        return fig

    def stamp_remover(self) -> None:
        stamp_path = os.path.join(self.path_tmp, 'stamp.png')
        os.remove(stamp_path)


class Stamper:
    def __init__(self, name, importer: Importer):
        self.name = name
        self.df   = importer.df
        self.path_tmp = importer.path_tmp
        self.path_output = importer.path_output
        self.doc = importer.doc

        self.file_path = self._file_path_creator()

        # ✓ Bildgröße mit context manager auslesen (schließt automatisch)
        stamp_path = os.path.join(self.path_tmp, 'stamp.png')
        with Image.open(stamp_path) as img:
            self.stamp_width, self.stamp_height = img.size

        # ✓ ENTFERNT: _page_extractor() - wird nicht mehr benötigt
        
    def _file_path_creator(self):
        clean_title = str(self.df.loc[self.name, 'Titel']).strip()  # ✓ KORRIGIERT
        clean_date  = str(self.df.loc[self.name, 'Datum']).strip()  # ✓ KORRIGIERT
        file_name   = f'{clean_date}_{self.name}_{clean_title}.pdf'

        path = os.path.join(self.path_tmp, self.name, file_name)

        return path
    
    def stamp_and_save(self, position=(400, 100), max_width=200):
        """
        Stempelt die Seite und speichert sie im tmp/<Name>/ Ordner
        (überschreibt die Original-Datei ohne Suffix)
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
        
        stamp_path = os.path.join(self.path_tmp, 'stamp.png')
        
        # Output-Pfad ist gleich Input-Pfad (im tmp/<Name>/ Ordner)
        output_path = self.file_path
        
        # Temporärer Pfad für sichere Speicherung
        temp_path = output_path + '.tmp'
        
        print(f"Speichere nach: {output_path}")
        
        # ✓ Dokument EINMALIG öffnen, stempeln, temporär speichern und schließen
        doc = pymupdf.open(self.file_path)
        doc[0].insert_image(img_rect, filename=stamp_path)
        doc.save(temp_path)
        doc.close()
        
        # ✓ Original löschen und temporäre Datei umbenennen
        os.remove(output_path)
        os.rename(temp_path, output_path)
        
        print(f"✓ Gestempelte PDF gespeichert (Original überschrieben)")


class Resampler:
    def __init__(self, importer: Importer):
        self.df = importer.df
        self.path_tmp = importer.path_tmp
        self.doc = importer.doc

    def folder_creator(self) -> None:
        for name in self.df.index:
            path = os.path.join(self.path_tmp, name)
            os.makedirs(path, exist_ok=True)

    def spliter(self) -> None:
        for name in self.df.index:
            start_page = int(self.df.loc[name, 'First'] - 1)
            end_page = int(self.df.loc[name, 'Last'] - 1)
            
            new_doc = pymupdf.open()
            new_doc.insert_pdf(self.doc, from_page=start_page, to_page=end_page)
            
            clean_title = str(self.df.loc[name, 'Titel']).strip()
            clean_date = str(self.df.loc[name, 'Datum']).strip()
            file_name = f'{clean_date}_{name}_{clean_title}.pdf'
            
            save_path = os.path.join(self.path_tmp, name, file_name)
            new_doc.save(save_path)
            new_doc.close()


if __name__ == '__main__':
    # Importer erstellen
    importer = Importer()
    print(importer.df.head())
    
    # Resampler mit Importer-Instanz
    sampler = Resampler(importer)
    sampler.folder_creator()
    sampler.spliter()
    
    # Über alle Schüler iterieren
    for name in importer.df.index:
        print(f"\nVerarbeite {name}...")
        
        # StampCreator mit Importer-Instanz
        stamp = StampCreator(name, importer)
        stamp.boxplot()
        
        # Stamper mit Importer-Instanz
        stamp_pad = Stamper(name, importer)
        stamp_pad.stamp_and_save()
        
        # ✓ Kleine Pause für Windows
        time.sleep(0.1)
        
        # ✓ Aufräumen (wieder aktiviert)
        stamp.stamp_remover()
        
        print(f"✓ {name} fertig!")
    
    # Dokument schließen
    importer.doc.close()
    
    print("\n=== Alle Schüler verarbeitet ===")
    input('Enter drücken, um die Anzeige zu beenden.')

