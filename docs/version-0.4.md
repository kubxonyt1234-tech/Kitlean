# Kitlean 0.4 Beta — gry 2D

To rozszerzenie interpretera 0.1–0.3. Wszystkie zasoby przykładów są dołączone. Uruchom `START.bat` lub `kitlean run examples/infinite_world.kit` po instalacji. WSAD porusza postacią, ESC zamyka demo.

## Tworzenie, parametry i tekst

```kitlean
[create gui.menu/$Moja gra$="game"]
game.size=(640,400)
game.background=#E7F3E8
[create item.sprite/assets/player.png="player"]
player.position=(100,100)
player.setting.move=wsad/120
player.collision=true
game.camera.follow=player
game.camera.zoom=1.5
when key.ESCAPE.pressed:
    close.app
run game
```

`create gui.menu/Gra` i `create item.button/KLIKNIJ!` tworzą obiekt bez aliasu. Nawiasy kwadratowe pozwalają nadać alias. Teksty `/Napis`, `/$Punkty: {points}$`, `.text/Napis` pozostają oddzielone od parametrów `.size=(800,600)`, `.visible=true`. Kolory #RRGGBB bez cudzysłowów działają dla background i color; poza tym # oznacza komentarz. Jawny alias ma pierwszeństwo przed skrótem typu.

Zgodność: stare `create item.button/"Napis"` zmienia ostatni przycisk; nowy zapis z gołym tekstem lub `$...$` tworzy kolejny. Zachowano starsze `if button.clicked`, `key/SPACE.pressed`, `create item/button` i wcześniejsze CLI. Nowe programy dzielą przez `:`. Stare `/` i `//` pozostają wyjątkami zgodności — pełna zgodność ze starymi plikami wyklucza całkowite usunięcie tych operatorów.

## Akcje i zdarzenia

```kitlean
player.action.move(10,0)
player.action.teleport(100,100)
player.action.rotate(45)
player.action.hide
player.action.show
player.animation.speed=2
player.animation.loop=true
player.action.animate(bounce)
when player.animation.finished:
    print($Animacja skończona$)
when mouse.left.clicked:
    print(mouse.position)
when player.collided.enemy1:
    player.action.hide
```

move przesuwa, teleport ustawia pozycję. rotate dodaje stopnie (sprite lub image). hide/show dotyczą elementów GUI. Zdarzenia rejestrują blok, nie są odczytywalnymi flagami. Kolizja emituje zdarzenie przy rozpoczęciu kontaktu; ponowny kontakt po rozdzieleniu emituje kolejne. Mysz obsługuje left/right.clicked, a mouse.position zwraca pozycję w układzie widocznego GUI. Sprite obsługuje także clicked/hovered.

Animacje sprite: bounce (wizualne odbicie o 12 jednostek), rotate (pełny obrót), fade (zanikanie do zera). animation.speed to cykle na sekundę, animation.loop powtarza cykl. Zdarzenie finished występuje po cyklu. Ukryte sprite’y wstrzymują symulację i animację. Obrót i bounce zmieniają obraz, nie prostokąt kolizji.

## Ruch i fizyka

Pozycja to lewy górny róg w logicznych pikselach świata. `player.setting.move=wsad/120` lub `arrows/120` ustawia schemat i prędkość w jednostkach/s. Prędkość można później zmienić przez `.speed=...`. Ruch po przekątnej jest normalizowany. Aktualizacja fizyki ma krok 1/120 s, odrysowanie około 60 Hz. Kamera nie zmienia współrzędnych obiektów; follow centruje wskazany sprite, zoom skaluje obraz.

```kitlean
player.gravity=120
when key.SPACE.pressed:
    player.action.jump(100)
```

Grawitacja działa w dół, w jednostkach/s². Dolna krawędź menu stanowi podłoże dla obiektu z grawitacją; nieruchome sprite’y z collision=true mogą być platformami. Skok wymaga dodatniej grawitacji i mocy, działa tylko na podłożu. Nie ma podwójnego skoku. Kolizje to osiowe prostokąty AABB i rozwiązywanie ruchu po osiach. To prosta fizyka: brak mas, obrotowych brył, tarcia i ciągłego wykrywania zderzeń; bardzo szybki obiekt może przeskoczyć cienką przeszkodę. Wiele aktywnych obiektów zwiększa koszt parowych testów.

## Szablony, kopie i NPC

```kitlean
[create item.sprite/assets/zombie.png="zombie"]
zombie.collision=true
zombie.save=npc
[summon random.npc/zombie="enemy1"]
enemy1.speed=5
summon npc/zombie=(300,200)
summon npc/zombie=player
summon random.npc/zombie=game
create player.copy
del sprite
```

save=npc zapisuje kopię konfiguracji i wyłącza źródło z renderowania oraz kolizji. Każda instancja jest niezależna; zmiana enemy1 nie zmienia szablonu. Usunięcie źródła nie usuwa zarejestrowanego szablonu. Prędkość NPC nie oznacza AI ani pościgu. create player.copy tworzy kopię z automatycznym aliasem (skrót sprite wskazuje nową instancję). copy kopiuje konfigurację i stan animacji/ruchu, ale nie rejestracje handlerów. del usuwa obiekt, widget, powiązania, kontakty i jego handlery.

Losowanie szuka wolnej pozycji wewnątrz menu, maksymalnie 100 prób. Wariant =player losuje w pobliżu wskazanego sprite’a; =game wybiera mapę. Zbyt duży obiekt, pełna mapa lub zajęta jawna pozycja zgłasza błąd. Przy kilku spawnach najpierw zarezerwuj stałe pozycje, potem losuj. Aliasy instancji bez podanej nazwy generowane są automatycznie.

## Segmenty i thene

```kitlean
repeat forever:
    if player.outof.gui.game:
        create game.gui.next
        thene summon random.npc/zombie
        thene del game.last=copy
```

repeat forever działa kooperacyjnie raz na klatkę. Wyjście prostokąta player poza logiczną krawędź menu (nie krawędź kamery) zapamiętuje kierunek. create game.gui.next przechodzi do sąsiada w lewo/prawo/górę/dół. Przenosi ten sam obiekt gracza na przeciwną krawędź. Jeden kontakt z krawędzią powoduje jedno przejście. Wciąż istnieje jedno okno i jeden Canvas.

Segmenty dostają stabilne identyfikatory game, game1, game2… powiązane ze współrzędnymi siatki. Nie są osobnymi GUI do otwierania. game.last wskazuje poprzedni identyfikator. Baza SQLite zapisuje sprite’y, ich właściwości, stan ruchu/animacji i tło. Powrót odtwarza poprzedni segment. Gracz podróżuje, widgety HUD są wspólne, a źródła szablonów pozostają zarejestrowane. Handlery nie są serializowane jako kod.

Przejście najpierw sprawdza dane i zapisuje segment; dopiero potem usuwa jego żywe obiekty. `thene del game.last=copy` potwierdza bezpieczne zwolnienie zapisanego poprzednika (operacja idempotentna), nie trzyma drugiej kopii GUI. Błędy pliku lub konflikt identyfikatora wykrywane są przed zmianą aktywnego świata. Żywe obiekty należą do aktualnego segmentu, bufor obrazów źródłowych ma limit 32, cache SQLite około 512 KiB. Plik bazy rośnie z liczbą odwiedzonych pól; „nieskończony” oznacza generowanie na żądanie i ograniczenie aktywnego świata, nie nieskończoną pojemność dysku.

Baza leży obok danych zapisu konkretnego programu (`world_game.sqlite3`). Zachowuje odwiedzone snapshoty między uruchomieniami. Segment startowy i gracz są jednak tworzeni ze źródła przy każdym starcie: nie jest to pełny save-game aktualnej pozycji i całej sesji. Nie uruchamiaj równocześnie kilku zapisujących kopii tego samego projektu.

thene wykonuje następną instrukcję po sukcesie poprzedniej, w tym po zakończeniu wait. Nie jest osobnym wątkiem ani transakcją cofającą wcześniejsze efekty. Błąd przerywa ciąg; wynik false pomija dalszy łańcuch. Nie używaj thene bez poprzedniej wykonywalnej instrukcji ani po deklaracji funkcji/eventu/forever. animate zwraca sukces po uruchomieniu animacji; na koniec animacji czeka się zdarzeniem finished. Przy odtworzonym segmencie `thene summon` w łańcuchu przejścia jest pomijane, aby nie dublować zapisanych NPC. Samodzielne summon nadal tworzy nową instancję.

## Wygląd GUI

```kitlean
[create item.button/$GRAJ!$="play"]
play.background=#FF6600
play.color=#FFFFFF
play.rounded=14
play.align=center
play.margin=20
game.fullscreen=true
```

Przyciski korzystają z Canvas i rzeczywistej maski zaokrąglenia Pillow. align to left/center/right, margin wyznacza margines układu. Ręczne position ma pierwszeństwo. Nie jest to edytor poziomów ani rozbudowany system responsywnego UI. Zachowano audio, JSON, input, checkboxy, timery i funkcje matematyczne 0.3. Nie sprawdzono każdego komputera, wersji Windows i DPI.
