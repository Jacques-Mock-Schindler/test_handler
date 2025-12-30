"""
Stamper - Ein Tool zum automatisierten Stempeln von PDF-Korrekturfahnen.

Dieses Modul ermöglicht das Hinzufügen von individuellen Notenstempeln zu
PDF-Dokumenten und die Organisation der gestempelten Dateien nach Schülernamen.
"""

import pandas as pd
import matplotlib.pyplot as plt
import pymupdf
import io
from pathlib import Path


class Pathfinder:
    """
    Verwaltet Dateipfade für Eingabe- und Ausgabedateien.
    
    Diese Klasse sammelt Pfade für das PDF-Dokument, die CSV-Datentabelle
    und den Zielordner durch Benutzereingaben oder Standardwerte.
    """
    
    def __init__(self):
        """Initialisiert Pathfinder und sammelt alle benötigten Pfade."""
        self.doc = self._doc_path_collector()
        self.data = self._data_path_collector()
        self.destination_folder = self._destination_folder_path_collector()

    def _path_collector(self, default: str, input_text: str) -> str:
        """
        Sammelt einen Dateipfad vom Benutzer oder verwendet den Standardwert.
        
        Args:
            default: Der Standardpfad, falls keine Eingabe erfolgt.
            input_text: Der Text, der dem Benutzer angezeigt wird.
            
        Returns:
            Der vom Benutzer eingegebene Pfad oder der Standardwert.
        """
        user_path = input(input_text)
        
        # Verwende Standardpfad bei leerer Eingabe
        if user_path == '':
            return default
        else:
            return user_path

    def _data_path_collector(self) -> str:
        """
        Sammelt den Pfad zur CSV-Notentabelle.
        
        Returns:
            Pfad zur Notentabelle (Standard: './data/steuerung.csv').
        """
        default = './data/steuerung.csv'
        input_text = 'Geben Sie hier den Pfad zur Notentabelle ein: '
        
        return self._path_collector(default, input_text)
        
    def _doc_path_collector(self) -> str:
        """
        Sammelt den Pfad zur PDF-Korrekturfahne.
        
        Returns:
            Pfad zur Korrekturfahne (Standard: './data/fahne.pdf').
        """
        default = './data/fahne.pdf'
        input_text = 'Geben Sie hier den Pfad zur Korrekturfahne ein: '
        
        return self._path_collector(default, input_text)
        
    def _destination_folder_path_collector(self) -> str:
        """
        Sammelt den Pfad zum Zielordner für gestempelte Dateien.
        
        Returns:
            Pfad zum Ausgabeordner (Standard: './data/output/').
        """
        default = './data/output/'
        input_text = ('Geben Sie hier den Pfad zum Speicherort der '
                      'gestempelten Dateien an (ohne Unterordner): ')
                      
        return self._path_collector(default, input_text)


class DataHandler:
    """
    Verarbeitet und bereinigt die Notendaten aus der CSV-Datei.
    
    Diese Klasse lädt die CSV-Datei, entfernt fehlende Werte, normalisiert
    Umlaute und bereitet die Daten für die weitere Verarbeitung vor.
    """
    
    def __init__(self, paths: Pathfinder):
        """
        Initialisiert DataHandler und lädt die Daten.
        
        Args:
            paths: Ein Pathfinder-Objekt mit den Dateipfaden.
        """
        self.df = self._df_fetcher(paths)
        self.df = self._df_cleaner()
        
    def _df_fetcher(self, paths: Pathfinder) -> pd.DataFrame:
        """
        Lädt die CSV-Datei in einen pandas DataFrame.
        
        Args:
            paths: Ein Pathfinder-Objekt mit dem Pfad zur CSV-Datei.
            
        Returns:
            DataFrame mit den rohen Notendaten.
        """
        df = pd.read_csv(paths.data,
                         sep=';',
                         encoding='utf-8')
        
        return df
        
    def _df_cleaner(self) -> pd.DataFrame:
        """
        Bereinigt und normalisiert den DataFrame.
        
        Entfernt fehlende Werte, standardisiert Spaltennamen,
        ersetzt Umlaute durch ASCII-Äquivalente und setzt den
        Nachnamen als Index.
        
        Returns:
            Bereinigter und normalisierter DataFrame.
        """
        df = self.df
        
        # Entferne Zeilen mit fehlenden Werten
        df = df.dropna()
        
        # Standardisiere Spaltennamen (Nachname -> Name)
        df = df.rename(columns=lambda x: x.replace('Nachname', 'Name') 
                       if x.startswith('Nach') else x)

        # Erstelle Mapping für Umlaute zu ASCII-Zeichen
        umlaute_map = str.maketrans({
            'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
            'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
        })
        
        # Ersetze Umlaute in Nachnamen
        df['Name'] = df['Name'].str.translate(umlaute_map)

        # Setze Nachname als Index für schnellen Zugriff
        df = df.set_index('Name')

        return df


class Stamper:
    """
    Erstellt und platziert Notenstempel auf PDF-Seiten.
    
    Diese Klasse generiert Boxplot-Visualisierungen mit individuellen Noten
    und fügt sie als Stempel in das PDF-Dokument ein.
    """
    
    def __init__(self, paths: Pathfinder, data: DataHandler):
        """
        Initialisiert Stamper mit Pfaden und Notendaten.
        
        Args:
            paths: Ein Pathfinder-Objekt mit Dateipfaden.
            data: Ein DataHandler-Objekt mit den Notendaten.
        """
        self.df = data.df
        self.doc = pymupdf.open(paths.doc)
        
    def _stamp_background_creator(self) -> plt.Figure:
        """
        Erstellt den Hintergrund des Stempels mit einem Boxplot.
        
        Erzeugt einen Boxplot der Klassenleistung mit farblicher Kodierung:
        - Grün: Q1 > 4 (gute Leistung)
        - Rot: Q3 < 4 (schwache Leistung)
        - Orange: gemischte Leistung
        
        Returns:
            Matplotlib Figure-Objekt mit dem Boxplot.
        """
        # Erstelle Figure und Axes
        fig, ax = plt.subplots()

        # Berechne Quartile für Farbauswahl
        q1 = self.df['Note'].quantile(0.25)
        q3 = self.df['Note'].quantile(0.75)

        # Bestimme Farbe basierend auf Klassenleistung
        if q1 > 4:
            box_color = 'green'  # Sehr gute Klassenleistung
        elif q3 < 4:
            box_color = 'red'  # Schwache Klassenleistung
        else:
            box_color = 'orange'  # Durchschnittliche Leistung

        # Erstelle horizontalen Boxplot
        bplot = ax.boxplot(self.df['Note'], 
                           vert=False, 
                           patch_artist=True,
                           medianprops={
                               'color': 'red',
                               'linewidth': 3,
                               'linestyle': '-',
                           })
        
        # Setze Farbe und Transparenz der Box
        bplot['boxes'][0].set_facecolor(box_color)
        bplot['boxes'][0].set_alpha(0.6)
        
        # Entferne Y-Achsen-Beschriftung
        ax.set_yticks([])
        ax.set_xlabel('Note')
        
        return fig
    
    def _create_stamp(self, name: str, fig: plt.Figure) -> plt.Figure:
        """
        Erstellt einen individualisierten Stempel für einen Schüler.
        
        Fügt die individuelle Note als Punkt, eine Tabelle mit Punkten
        und Note sowie einen personalisierten Titel hinzu.
        
        Args:
            name: Nachname des Schülers.
            fig: Figure-Objekt mit dem Boxplot-Hintergrund.
            
        Returns:
            Vollständiges Figure-Objekt mit individualisiertem Stempel.
        """
        # Hole individuelle Notendaten
        individuelle_note = self.df.loc[name, 'Note']
        vorname = self.df.loc[name, 'Vorname']
        ax = fig.axes[0]
        
        # Extrahiere Werte für Tabelle
        val_total = self.df.loc[name, 'Total']
        val_note = self.df.loc[name, 'Note']

        # Definiere Tabelleninhalt
        cell_text = [
            ['Punkte', f"{val_total}"],
            ['Note', f"{val_note}"]
        ]

        # Erstelle Tabelle mit Punkten und Note
        table = ax.table(
            cellText=cell_text,
            loc='upper center',
            cellLoc='left',
            colWidths=[0.2, 0.2]
        )
        
        # Entferne Tabellenlinien für saubereres Design
        for cell in table.get_celld().values():
            cell.set_linewidth(0)
        table.scale(1, 2)
        table.set_fontsize(12)
        
        # Markiere individuelle Note mit blauem Punkt
        ax.scatter(
            x=individuelle_note,
            y=1,
            color='blue',
            marker='o',
            s=75,
            zorder=3,  # Stelle sicher, dass Punkt über Boxplot liegt
        )
        
        # Setze personalisierten Titel
        ax.set_title(f'{vorname}s Note vor dem Hintergrund der Klassenleistung')
        
        return fig
    
    def _apply_stamp(self, page_number: int, fig: plt.Figure) -> None:
        """
        Fügt den Stempel auf einer bestimmten PDF-Seite ein.
        
        Args:
            page_number: Seitennummer (0-basiert) für den Stempel.
            fig: Figure-Objekt mit dem vollständigen Stempel.
        """
        doc = self.doc
        buf = io.BytesIO()
        
        # Berechne Seitenverhältnis für korrekte Skalierung
        width_in, height_in = fig.get_size_inches()
        aspect_ratio = height_in / width_in
        
        # Definiere Stempelgröße und Position
        stamp_width = 200 
        stamp_height = stamp_width * aspect_ratio
        
        x_start = 400
        y_start = 100
        position_rect = pymupdf.Rect(x_start, y_start, 
                                     x_start + stamp_width, 
                                     y_start + stamp_height)
        
        # Speichere Figure als PNG in Buffer
        fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
        buf.seek(0)
        
        # Füge Bild auf PDF-Seite ein
        page = doc[page_number]
        page.insert_image(position_rect, stream=buf)
        
        buf.close()
        
    def printing_press(self) -> None:
        """
        Verarbeitet alle Schüler und fügt Stempel in das PDF ein.
        
        Iteriert durch alle Schüler im DataFrame, erstellt individuelle
        Stempel und speichert das gestempelte PDF.
        """
        # Iteriere durch alle Schüler
        for name in self.df.index:
            # Erstelle frischen Hintergrund für jeden Stempel
            fresh_fig = self._stamp_background_creator()
            # Erstelle individualisierten Stempel
            stamp = self._create_stamp(name, fresh_fig)
            # Hole Seitennummer (1-basiert -> 0-basiert)
            page_number = int(self.df.loc[name, 'First']) - 1
            # Füge Stempel ein
            self._apply_stamp(page_number, stamp)
            # Schließe Figure um Speicher freizugeben
            plt.close(stamp)
        
        # Speichere gestempeltes PDF mit Kompression
        self.doc.save('./data/fahne_gestempelt.pdf', garbage=4, deflate=True)


class FileManager:
    """
    Organisiert gestempelte PDF-Dateien in individuelle Ordner.
    
    Diese Klasse erstellt für jeden Schüler einen Ordner und
    extrahiert die entsprechenden Seiten aus dem gestempelten PDF.
    """
    
    def __init__(self, paths: Pathfinder, df: DataHandler) -> None:
        """
        Initialisiert FileManager mit Pfaden und Daten.
        
        Args:
            paths: Ein Pathfinder-Objekt mit Dateipfaden.
            df: Ein DataHandler-Objekt mit den Notendaten.
        """
        self.path = paths.destination_folder
        self.df = df.df
        
    def folder_creator(self) -> None:
        """
        Erstellt für jeden Schüler einen eigenen Ordner.
        
        Die Ordner werden nach dem Nachnamen des Schülers benannt.
        Existierende Ordner werden nicht überschrieben.
        """
        for name in self.df.index:
            # Erstelle Pfad mit Schülername
            path = Path(self.path) / name
            # Erstelle Ordner (inkl. übergeordnete Ordner falls nötig)
            Path(path).mkdir(parents=True, exist_ok=True)
            
    def file_distributor(self) -> None:
        """
        Verteilt gestempelte Seiten in individuelle PDF-Dateien.
        
        Extrahiert für jeden Schüler die entsprechenden Seiten aus dem
        gestempelten PDF und speichert sie mit aussagekräftigem Dateinamen
        im jeweiligen Schülerordner. Löscht anschließend das temporäre
        gestempelte PDF.
        """
        # Öffne gestempeltes Quelldokument
        src_doc = pymupdf.open('./data/fahne_gestempelt.pdf')
        
        # Iteriere durch alle Schüler
        for name in self.df.index:
            # Extrahiere Metadaten für Dateinamen
            date = str(self.df.loc[name, 'Datum'])
            title = str(self.df.loc[name, 'Titel'])
            file_title = f'{date}_{name}_{title}.pdf'
            
            # Bestimme Seitenbereich (1-basiert -> 0-basiert)
            start_page = int(self.df.loc[name, 'First']) - 1
            end_page = int(self.df.loc[name, 'Last']) - 1
            
            # Erstelle Zielpfad
            path = Path(self.path) / name / file_title
            
            # Erstelle neues PDF-Dokument
            new_doc = pymupdf.open()
            # Füge relevante Seiten ein
            new_doc.insert_pdf(src_doc, from_page=start_page, to_page=end_page)
            # Speichere individuelles PDF
            new_doc.save(path)
        
        # Schließe Quelldokument
        src_doc.close()
        
        # Lösche temporäres gestempeltes PDF
        pdf_path = Path('./data/fahne_gestempelt.pdf')
        pdf_path.unlink(missing_ok=True)


if __name__ == '__main__':
    # Initialisiere Pfadverwaltung
    paths = Pathfinder()
    
    # Lade und bereite Notendaten auf
    data = DataHandler(paths)
    print(data.df.head())
    
    # Erstelle Stempel-Engine
    stamp = Stamper(paths, data)
    
    # Führe Stempelprozess aus
    stamp.printing_press()
    
    # Erstelle Dateimanager für Organisation
    file_manager = FileManager(paths, data)
    
    # Erstelle individuelle Ordner
    file_manager.folder_creator()
    
    # Verteile gestempelte Dateien
    file_manager.file_distributor()
    
    # Warte auf Benutzerbestätigung vor Programmende
    input('Zum Beenden des Programms ENTER drücken.')
