# core.py
import pandas as pd
import matplotlib.pyplot as plt

class Importer:
    def __init__(self) -> None:
        path = self._path_dialog()
        self.df = pd.read_csv(path, sep=';', encoding='utf-8')
        self.df = self._df_cleaner()
        
        
    def _path_dialog(self, path: str ='./data/steuerung.csv') -> str:
        path_input = input("Geben Sie den Pfad zu Ihrer Steuerdatei ein: ")

        if path_input == "":
            path_input = path

        return path_input

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


class Stamp:
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

        # Set labels and title
        # ax.set_xlabel('Temperature')
        # ax.set_title('Simple Boxplot')

        # Show the plot
        return fig

    

if __name__ == '__main__':
    # path = input('Pfad hier eingeben: ')
    test   = Importer()
    print(test.df.head())
    name = input('Namen eingeben: ')
    stamp = Stamp(name, test.df)
    plot = stamp.boxplot()
    plot.show()
    input('Enter drüken, um die Anzeige zu beenden.')