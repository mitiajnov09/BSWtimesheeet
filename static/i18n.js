'use strict';
// Only interface strings are translated. Names, notes and other saved data stay intact.
const LANGUAGE_OPTIONS=[['ru','Русский'],['lt','Lietuvių'],['pl','Polski']];
let language=localStorage.getItem('rotations-language')||'ru';
if(!LANGUAGE_OPTIONS.some(([code])=>code===language))language='ru';
const UI_TRANSLATIONS={
  "Ротации": [
    "Rotacijos",
    "Rotacje"
  ],
  "Рабочее пространство": [
    "Darbo sritis",
    "Obszar roboczy"
  ],
  "График ротаций": [
    "Rotacijų grafikas",
    "Grafik rotacji"
  ],
  "Проекты": [
    "Projektai",
    "Projekty"
  ],
  "Работники": [
    "Darbuotojai",
    "Pracownicy"
  ],
  "Учётные записи": [
    "Naudotojų paskyros",
    "Konta użytkowników"
  ],
  "История изменений": [
    "Pakeitimų istorija",
    "Historia zmian"
  ],
  "Индивидуальные циклы": [
    "Individualūs ciklai",
    "Indywidualne cykle"
  ],
  "Рабочие дни и дни отдыха": [
    "Darbo ir poilsio dienos",
    "Dni pracy i odpoczynku"
  ],
  "под контролем команды.": [
    "kontroliuojamos komandos.",
    "pod kontrolą zespołu."
  ],
  "Администратор": [
    "Administratorius",
    "Administrator"
  ],
  "Руководитель проекта": [
    "Projekto vadovas",
    "Kierownik projektu"
  ],
  "Руководитель": [
    "Vadovas",
    "Kierownik"
  ],
  "Сменить пароль": [
    "Keisti slaptažodį",
    "Zmień hasło"
  ],
  "Выйти": [
    "Atsijungti",
    "Wyloguj"
  ],
  "Данные сохранены": [
    "Duomenys išsaugoti",
    "Dane zapisane"
  ],
  "Обновить данные": [
    "Atnaujinti duomenis",
    "Odśwież dane"
  ],
  "Данные обновлены": [
    "Duomenys atnaujinti",
    "Dane odświeżone"
  ],
  "Изменения сохранены": [
    "Pakeitimai išsaugoti",
    "Zmiany zapisane"
  ],
  "Планируйте работу и отдых вашей команды": [
    "Planuokite komandos darbą ir poilsį",
    "Planuj pracę i odpoczynek zespołu"
  ],
  "Экспорт в PDF": [
    "Eksportuoti į PDF",
    "Eksport do PDF"
  ],
  "Запланировать": [
    "Planuoti",
    "Zaplanuj"
  ],
  "Активный проект": [
    "Aktyvus projektas",
    "Aktywny projekt"
  ],
  "В архиве": [
    "Archyve",
    "W archiwum"
  ],
  "Неактивный": [
    "Neaktyvus",
    "Nieaktywny"
  ],
  "Неактивные работники": [
    "Neaktyvūs darbuotojai",
    "Nieaktywni pracownicy"
  ],
  "Всего работников": [
    "Darbuotojų skaičius",
    "Liczba pracowników"
  ],
  "в проекте": [
    "projekte",
    "w projekcie"
  ],
  "На объекте сегодня": [
    "Šiandien objekte",
    "Dzisiaj na obiekcie"
  ],
  "работают": [
    "dirba",
    "pracują"
  ],
  "Отдыхают сегодня": [
    "Šiandien ilsisi",
    "Dzisiaj odpoczywają"
  ],
  "работников": [
    "darbuotojų",
    "pracowników"
  ],
  "Ближайшие перелёты": [
    "Artimiausi skrydžiai",
    "Najbliższe loty"
  ],
  "за 7 дней": [
    "per 7 dienas",
    "w ciągu 7 dni"
  ],
  "Предыдущий период": [
    "Ankstesnis laikotarpis",
    "Poprzedni okres"
  ],
  "Следующий период": [
    "Kitas laikotarpis",
    "Następny okres"
  ],
  "Сегодня": [
    "Šiandien",
    "Dzisiaj"
  ],
  "Выбрать период": [
    "Pasirinkti laikotarpį",
    "Wybierz okres"
  ],
  "Масштаб": [
    "Mastelis",
    "Skala"
  ],
  "Месяц": [
    "Mėnuo",
    "Miesiąc"
  ],
  "Квартал": [
    "Ketvirtis",
    "Kwartał"
  ],
  "Год": [
    "Metai",
    "Rok"
  ],
  "квартал": [
    "ketvirtis",
    "kwartał"
  ],
  "год": [
    "metai",
    "rok"
  ],
  "Найти работника…": [
    "Ieškoti darbuotojo…",
    "Znajdź pracownika…"
  ],
  "Поиск работника": [
    "Darbuotojo paieška",
    "Wyszukaj pracownika"
  ],
  "Все специальности": [
    "Visos specialybės",
    "Wszystkie specjalności"
  ],
  "Фильтр по специальности": [
    "Filtruoti pagal specialybę",
    "Filtr specjalności"
  ],
  "Фильтр по статусу": [
    "Filtruoti pagal būseną",
    "Filtr statusu"
  ],
  "Активные работники": [
    "Aktyvūs darbuotojai",
    "Aktywni pracownicy"
  ],
  "Все статусы": [
    "Visos būsenos",
    "Wszystkie statusy"
  ],
  "Календарный график, прокручивается горизонтально": [
    "Kalendoriaus grafikas, slenkamas horizontaliai",
    "Grafik kalendarza, przewijany poziomo"
  ],
  "РАБОТНИК": [
    "DARBUOTOJAS",
    "PRACOWNIK"
  ],
  "НЕДЕЛЯ": [
    "SAVAITĖ",
    "TYDZIEŃ"
  ],
  "Работа": [
    "Darbas",
    "Praca"
  ],
  "Отдых": [
    "Poilsis",
    "Odpoczynek"
  ],
  "Отпуск": [
    "Atostogos",
    "Urlop"
  ],
  "Больничный": [
    "Nedarbingumas",
    "Zwolnienie lekarskie"
  ],
  "Ручная правка": [
    "Rankinis pakeitimas",
    "Zmiana ręczna"
  ],
  "Перелёт": [
    "Skrydis",
    "Lot"
  ],
  "дней": [
    "dienų",
    "dni"
  ],
  "Действия": [
    "Veiksmai",
    "Działania"
  ],
  "Нет работников, соответствующих фильтрам.": [
    "Nėra filtrus atitinkančių darbuotojų.",
    "Brak pracowników spełniających filtry."
  ],
  "Перетащите статус или перелёт из легенды на нужный день работника. При наложении появится дополнительный слой.": [
    "Nuvilkite būseną arba skrydį iš legendos į reikiamą darbuotojo dieną. Persidengus bus sukurtas papildomas sluoksnis.",
    "Przeciągnij status lub lot z legendy na wybrany dzień pracownika. Przy nakładaniu powstanie dodatkowa warstwa."
  ],
  "Перетащите полосу, чтобы изменить даты. Потяните за край, чтобы изменить длительность. Сб и Вс выделены фоном.": [
    "Nuvilkite juostą, kad pakeistumėte datas. Traukite kraštą, kad pakeistumėte trukmę. Šeštadieniai ir sekmadieniai pažymėti fonu.",
    "Przeciągnij pasek, aby zmienić daty. Pociągnij krawędź, aby zmienić długość. Soboty i niedziele wyróżniono tłem."
  ],
  "Январь": [
    "Sausis",
    "Styczeń"
  ],
  "Февраль": [
    "Vasaris",
    "Luty"
  ],
  "Март": [
    "Kovas",
    "Marzec"
  ],
  "Апрель": [
    "Balandis",
    "Kwiecień"
  ],
  "Май": [
    "Gegužė",
    "Maj"
  ],
  "Июнь": [
    "Birželis",
    "Czerwiec"
  ],
  "Июль": [
    "Liepa",
    "Lipiec"
  ],
  "Август": [
    "Rugpjūtis",
    "Sierpień"
  ],
  "Сентябрь": [
    "Rugsėjis",
    "Wrzesień"
  ],
  "Октябрь": [
    "Spalis",
    "Październik"
  ],
  "Ноябрь": [
    "Lapkritis",
    "Listopad"
  ],
  "Декабрь": [
    "Gruodis",
    "Grudzień"
  ],
  "Вс": [
    "Sk",
    "Nd"
  ],
  "Пн": [
    "Pr",
    "Pn"
  ],
  "Вт": [
    "An",
    "Wt"
  ],
  "Ср": [
    "Tr",
    "Śr"
  ],
  "Чт": [
    "Kt",
    "Cz"
  ],
  "Пт": [
    "Pn",
    "Pt"
  ],
  "Сб": [
    "Št",
    "Sb"
  ],
  "Каждый человек.": [
    "Kiekvienas žmogus.",
    "Każdy człowiek."
  ],
  "Каждая ротация.": [
    "Kiekviena rotacija.",
    "Każda rotacja."
  ],
  "В одном графике.": [
    "Viename grafike.",
    "W jednym grafiku."
  ],
  "Работа, отдых и перелёты вашей команды — с учётом проектов и индивидуальных циклов.": [
    "Komandos darbas, poilsis ir skrydžiai pagal projektus ir individualius ciklus.",
    "Praca, odpoczynek i loty zespołu z uwzględnieniem projektów i indywidualnych cykli."
  ],
  "Вход в систему": [
    "Prisijungimas",
    "Logowanie"
  ],
  "Планирование начинается здесь.": [
    "Planavimas prasideda čia.",
    "Planowanie zaczyna się tutaj."
  ],
  "Логин": [
    "Prisijungimo vardas",
    "Login"
  ],
  "Пароль": [
    "Slaptažodis",
    "Hasło"
  ],
  "Ваш логин": [
    "Jūsų prisijungimo vardas",
    "Twój login"
  ],
  "Ваш пароль": [
    "Jūsų slaptažodis",
    "Twoje hasło"
  ],
  "Войти": [
    "Prisijungti",
    "Zaloguj się"
  ],
  "Учётную запись создаёт администратор.": [
    "Paskyrą sukuria administratorius.",
    "Konto tworzy administrator."
  ],
  "Обратитесь к нему, если у вас ещё нет доступа.": [
    "Kreipkitės į jį, jei dar neturite prieigos.",
    "Skontaktuj się z nim, jeśli nie masz jeszcze dostępu."
  ],
  "Пока нет доступных проектов.": [
    "Nėra prieinamų projektų.",
    "Brak dostępnych projektów."
  ],
  "Создайте объект и проект в разделе «Проекты».": [
    "Sukurkite objektą ir projektą skiltyje „Projektai“.",
    "Utwórz obiekt i projekt w sekcji „Projekty”."
  ],
  "Открыть проекты": [
    "Atidaryti projektus",
    "Otwórz projekty"
  ],
  "Закрыть": [
    "Uždaryti",
    "Zamknij"
  ],
  "Отмена": [
    "Atšaukti",
    "Anuluj"
  ],
  "Сохранить": [
    "Išsaugoti",
    "Zapisz"
  ],
  "Контакты не указаны": [
    "Kontaktai nenurodyti",
    "Brak danych kontaktowych"
  ],
  "Построить цикл работы и отдыха": [
    "Sukurti darbo ir poilsio ciklą",
    "Utwórz cykl pracy i odpoczynku"
  ],
  "Добавить отдельный период": [
    "Pridėti atskirą laikotarpį",
    "Dodaj osobny okres"
  ],
  "Добавить перелёт или событие": [
    "Pridėti skrydį arba įvykį",
    "Dodaj lot lub wydarzenie"
  ],
  "Карточка работника": [
    "Darbuotojo kortelė",
    "Karta pracownika"
  ],
  "НАЗНАЧЕНИЯ НА ПРОЕКТ": [
    "PRISKYRIMAI PROJEKTUI",
    "PRZYDZIAŁY DO PROJEKTU"
  ],
  "Изменить назначение": [
    "Keisti priskyrimą",
    "Zmień przydział"
  ],
  "Запланировать ротацию": [
    "Planuoti rotaciją",
    "Zaplanuj rotację"
  ],
  "Работник": [
    "Darbuotojas",
    "Pracownik"
  ],
  "Настроить цикл": [
    "Nustatyti ciklą",
    "Ustaw cykl"
  ],
  "Цикл": [
    "Ciklas",
    "Cykl"
  ],
  "6 недель работы = 42 календарных дня. 2 недели отдыха = 14 дней. Ручные исключения сохраняются.": [
    "6 darbo savaitės = 42 kalendorinės dienos. 2 poilsio savaitės = 14 dienų. Rankinės išimtys išsaugomos.",
    "6 tygodni pracy = 42 dni kalendarzowe. 2 tygodnie odpoczynku = 14 dni. Ręczne wyjątki zostają zachowane."
  ],
  "Недель работы": [
    "Darbo savaitės",
    "Tygodnie pracy"
  ],
  "Недель отдыха": [
    "Poilsio savaitės",
    "Tygodnie odpoczynku"
  ],
  "Начало цикла": [
    "Ciklo pradžia",
    "Początek cyklu"
  ],
  "Окончание (или повторения)": [
    "Pabaiga (arba kartojimai)",
    "Koniec (lub powtórzenia)"
  ],
  "Количество повторений": [
    "Kartojimų skaičius",
    "Liczba powtórzeń"
  ],
  "Если заданы оба ограничения, цикл завершится по первому из них.": [
    "Jei nustatytos abi ribos, ciklas baigsis ties ankstesne.",
    "Jeśli ustawiono oba ograniczenia, cykl zakończy się przy wcześniejszym."
  ],
  "Посмотреть изменения": [
    "Peržiūrėti pakeitimus",
    "Zobacz zmiany"
  ],
  "Подтверждение нового цикла": [
    "Naujo ciklo patvirtinimas",
    "Potwierdzenie nowego cyklu"
  ],
  "Будет заменено": [
    "Bus pakeista",
    "Zostanie zastąpionych"
  ],
  "автоматических периодов и создано": [
    "automatinių laikotarpių ir sukurta",
    "okresów automatycznych i utworzonych"
  ],
  "Ручных исключений сохранится": [
    "Išsaugomų rankinių išimčių",
    "Zachowanych ręcznych wyjątków"
  ],
  "Периоды, которые будут заменены": [
    "Laikotarpiai, kurie bus pakeisti",
    "Okresy, które zostaną zastąpione"
  ],
  "Существующие периоды не затронуты.": [
    "Esami laikotarpiai nebus pakeisti.",
    "Istniejące okresy pozostaną bez zmian."
  ],
  "Новый график": [
    "Naujas grafikas",
    "Nowy grafik"
  ],
  "Применить цикл": [
    "Taikyti ciklą",
    "Zastosuj cykl"
  ],
  "Изменить период": [
    "Keisti laikotarpį",
    "Zmień okres"
  ],
  "Новый период": [
    "Naujas laikotarpis",
    "Nowy okres"
  ],
  "Статус периода": [
    "Laikotarpio būsena",
    "Status okresu"
  ],
  "Применить изменение": [
    "Taikyti pakeitimą",
    "Zastosuj zmianę"
  ],
  "Только этот период": [
    "Tik šis laikotarpis",
    "Tylko ten okres"
  ],
  "Этот и следующие автоматические": [
    "Šis ir vėlesni automatiniai",
    "Ten i kolejne automatyczne"
  ],
  "Дата начала": [
    "Pradžios data",
    "Data początku"
  ],
  "Дата окончания": [
    "Pabaigos data",
    "Data końca"
  ],
  "Примечание": [
    "Pastaba",
    "Notatka"
  ],
  "Даты включительно. При сдвиге следующих периодов длительность выбранного периода должна остаться прежней. Ручные исключения останутся на своих датах.": [
    "Datos įskaitytinai. Perkeliant vėlesnius laikotarpius pasirinkto laikotarpio trukmė negali keistis. Rankinės išimtys lieka savo datose.",
    "Daty włącznie. Przy przesuwaniu kolejnych okresów długość wybranego okresu musi pozostać taka sama. Ręczne wyjątki pozostają na swoich datach."
  ],
  "Удалить период": [
    "Pašalinti laikotarpį",
    "Usuń okres"
  ],
  "Удалить период?": [
    "Pašalinti laikotarpį?",
    "Usunąć okres?"
  ],
  "Удалить": [
    "Pašalinti",
    "Usuń"
  ],
  "Подтвердить сдвиг": [
    "Patvirtinti perkėlimą",
    "Potwierdź przesunięcie"
  ],
  "Выбранный период и": [
    "Pasirinktas laikotarpis ir",
    "Wybrany okres i"
  ],
  "следующих автоматических периодов будут изменены.": [
    "vėlesni automatiniai laikotarpiai bus pakeisti.",
    "kolejnych okresów automatycznych zostanie zmienionych."
  ],
  "Применить сдвиг": [
    "Taikyti perkėlimą",
    "Zastosuj przesunięcie"
  ],
  "В графике останется незаполненный промежуток. Удаление будет записано в историю.": [
    "Grafike liks neužpildytas tarpas. Pašalinimas bus įrašytas istorijoje.",
    "W grafiku pozostanie pusty przedział. Usunięcie zostanie zapisane w historii."
  ],
  "Событие": [
    "Įvykis",
    "Wydarzenie"
  ],
  "Новое событие": [
    "Naujas įvykis",
    "Nowe wydarzenie"
  ],
  "Тип события": [
    "Įvykio tipas",
    "Typ wydarzenia"
  ],
  "Дата": [
    "Data",
    "Data"
  ],
  "Время (необязательно)": [
    "Laikas (neprivalomas)",
    "Godzina (opcjonalnie)"
  ],
  "Часовой пояс": [
    "Laiko juosta",
    "Strefa czasowa"
  ],
  "Маршрут": [
    "Maršrutas",
    "Trasa"
  ],
  "Номер рейса": [
    "Skrydžio numeris",
    "Numer lotu"
  ],
  "Перелёт на объект": [
    "Skrydis į objektą",
    "Lot na obiekt"
  ],
  "Обратный перелёт": [
    "Skrydis atgal",
    "Lot powrotny"
  ],
  "Прибытие": [
    "Atvykimas",
    "Przyjazd"
  ],
  "Отъезд": [
    "Išvykimas",
    "Wyjazd"
  ],
  "Удалить событие": [
    "Pašalinti įvykį",
    "Usuń wydarzenie"
  ],
  "Удалить событие?": [
    "Pašalinti įvykį?",
    "Usunąć wydarzenie?"
  ],
  "Объекты, руководители и сроки работы": [
    "Objektai, vadovai ir darbo terminai",
    "Obiekty, kierownicy i terminy pracy"
  ],
  "Объект": [
    "Objektas",
    "Obiekt"
  ],
  "Проект": [
    "Projektas",
    "Projekt"
  ],
  "Открыть график": [
    "Atidaryti grafiką",
    "Otwórz grafik"
  ],
  "Изменить проект": [
    "Keisti projektą",
    "Edytuj projekt"
  ],
  "Назначить": [
    "Priskirti",
    "Przydziel"
  ],
  "Руководители": [
    "Vadovai",
    "Kierownicy"
  ],
  "Не назначены": [
    "Nepriskirti",
    "Nieprzydzieleni"
  ],
  "Проекты пока не созданы.": [
    "Projektai dar nesukurti.",
    "Nie utworzono jeszcze projektów."
  ],
  "ОБЪЕКТЫ": [
    "OBJEKTAI",
    "OBIEKTY"
  ],
  "Изменить объект": [
    "Keisti objektą",
    "Edytuj obiekt"
  ],
  "Новый объект": [
    "Naujas objektas",
    "Nowy obiekt"
  ],
  "Название объекта": [
    "Objekto pavadinimas",
    "Nazwa obiektu"
  ],
  "Страна": [
    "Šalis",
    "Kraj"
  ],
  "Город": [
    "Miestas",
    "Miasto"
  ],
  "Адрес": [
    "Adresas",
    "Adres"
  ],
  "Новый проект": [
    "Naujas projektas",
    "Nowy projekt"
  ],
  "Название проекта": [
    "Projekto pavadinimas",
    "Nazwa projektu"
  ],
  "Статус": [
    "Būsena",
    "Status"
  ],
  "Активный": [
    "Aktyvus",
    "Aktywny"
  ],
  "Начало проекта": [
    "Projekto pradžia",
    "Początek projektu"
  ],
  "Окончание проекта": [
    "Projekto pabaiga",
    "Koniec projektu"
  ],
  "Активных руководителей пока нет.": [
    "Aktyvių vadovų dar nėra.",
    "Nie ma jeszcze aktywnych kierowników."
  ],
  "При архивировании назначения и история графика сохраняются.": [
    "Archyvuojant priskyrimai ir grafiko istorija išsaugomi.",
    "Archiwizacja zachowuje przydziały i historię grafiku."
  ],
  "Карточки команды и история назначений": [
    "Komandos kortelės ir priskyrimų istorija",
    "Karty zespołu i historia przydziałów"
  ],
  "Добавить работника": [
    "Pridėti darbuotoją",
    "Dodaj pracownika"
  ],
  "Специальность": [
    "Specialybė",
    "Specjalność"
  ],
  "Проекты / назначения": [
    "Projektai / priskyrimai",
    "Projekty / przydziały"
  ],
  "Не назначен": [
    "Nepriskirtas",
    "Nieprzydzielony"
  ],
  "Изменить работника": [
    "Keisti darbuotoją",
    "Edytuj pracownika"
  ],
  "Назначить на проект": [
    "Priskirti projektui",
    "Przydziel do projektu"
  ],
  "Новый работник": [
    "Naujas darbuotojas",
    "Nowy pracownik"
  ],
  "Имя": [
    "Vardas",
    "Imię"
  ],
  "Фамилия": [
    "Pavardė",
    "Nazwisko"
  ],
  "Контактные данные": [
    "Kontaktiniai duomenys",
    "Dane kontaktowe"
  ],
  "Назначить работника": [
    "Priskirti darbuotoją",
    "Przydziel pracownika"
  ],
  "Начало назначения": [
    "Priskyrimo pradžia",
    "Początek przydziału"
  ],
  "Окончание назначения": [
    "Priskyrimo pabaiga",
    "Koniec przydziału"
  ],
  "Назначения на разные объекты не могут пересекаться. Чтобы завершить назначение, измените дату окончания, сохраняя исторические периоды.": [
    "Priskyrimai skirtingiems objektams negali persidengti. Norėdami baigti priskyrimą, pakeiskite pabaigos datą išsaugodami istorinius laikotarpius.",
    "Przydziały do różnych obiektów nie mogą się nakładać. Aby zakończyć przydział, zmień datę końca, zachowując historyczne okresy."
  ],
  "Доступ руководителей к проектам": [
    "Vadovų prieiga prie projektų",
    "Dostęp kierowników do projektów"
  ],
  "Добавить руководителя": [
    "Pridėti vadovą",
    "Dodaj kierownika"
  ],
  "Пользователь": [
    "Naudotojas",
    "Użytkownik"
  ],
  "Роль": [
    "Vaidmuo",
    "Rola"
  ],
  "Доступ": [
    "Prieiga",
    "Dostęp"
  ],
  "Все проекты": [
    "Visi projektai",
    "Wszystkie projekty"
  ],
  "Активен": [
    "Aktyvus",
    "Aktywny"
  ],
  "Отключён": [
    "Išjungtas",
    "Wyłączony"
  ],
  "Изменить пользователя": [
    "Keisti naudotoją",
    "Edytuj użytkownika"
  ],
  "Изменить учётную запись": [
    "Keisti paskyrą",
    "Edytuj konto"
  ],
  "Новый руководитель": [
    "Naujas vadovas",
    "Nowy kierownik"
  ],
  "Имя и фамилия": [
    "Vardas ir pavardė",
    "Imię i nazwisko"
  ],
  "Новый пароль (необязательно)": [
    "Naujas slaptažodis (neprivalomas)",
    "Nowe hasło (opcjonalnie)"
  ],
  "Учётная запись активна": [
    "Paskyra aktyvi",
    "Konto aktywne"
  ],
  "Проекты назначаются в карточке проекта. Отключение немедленно завершит все сессии пользователя.": [
    "Projektai priskiriami projekto kortelėje. Išjungus paskyrą visos naudotojo sesijos iškart baigiamos.",
    "Projekty przypisuje się w karcie projektu. Wyłączenie natychmiast zakończy wszystkie sesje użytkownika."
  ],
  "Текущий пароль": [
    "Dabartinis slaptažodis",
    "Obecne hasło"
  ],
  "Новый пароль": [
    "Naujas slaptažodis",
    "Nowe hasło"
  ],
  "Повторите новый пароль": [
    "Pakartokite naują slaptažodį",
    "Powtórz nowe hasło"
  ],
  "После смены пароля потребуется войти заново.": [
    "Pakeitus slaptažodį reikės prisijungti iš naujo.",
    "Po zmianie hasła trzeba zalogować się ponownie."
  ],
  "Новые пароли не совпадают.": [
    "Nauji slaptažodžiai nesutampa.",
    "Nowe hasła nie są takie same."
  ],
  "Пароль изменён. Войдите с новым паролем.": [
    "Slaptažodis pakeistas. Prisijunkite su nauju slaptažodžiu.",
    "Hasło zmienione. Zaloguj się nowym hasłem."
  ],
  "Экспорт графика в PDF": [
    "Grafiko eksportas į PDF",
    "Eksport grafiku do PDF"
  ],
  "Начало периода": [
    "Laikotarpio pradžia",
    "Początek okresu"
  ],
  "Окончание периода": [
    "Laikotarpio pabaiga",
    "Koniec okresu"
  ],
  "Бумага": [
    "Popierius",
    "Papier"
  ],
  "альбомная": [
    "gulsčias",
    "poziomo"
  ],
  "Все работники": [
    "Visi darbuotojai",
    "Wszyscy pracownicy"
  ],
  "Выбранные работники": [
    "Pasirinkti darbuotojai",
    "Wybrani pracownicy"
  ],
  "Включить примечания": [
    "Įtraukti pastabas",
    "Uwzględnij notatki"
  ],
  "Включить перелёты и события": [
    "Įtraukti skrydžius ir įvykius",
    "Uwzględnij loty i wydarzenia"
  ],
  "Полный диапазон будет разбит на читаемые страницы. Имена и заголовки повторяются; детали перелётов и примечания — в приложении.": [
    "Visas laikotarpis bus padalintas į aiškius puslapius. Vardai ir antraštės kartojami; skrydžių informacija ir pastabos pateikiamos priede.",
    "Cały zakres zostanie podzielony na czytelne strony. Nazwiska i nagłówki są powtarzane; szczegóły lotów i notatki są w załączniku."
  ],
  "Скачать PDF": [
    "Atsisiųsti PDF",
    "Pobierz PDF"
  ],
  "PDF сформирован": [
    "PDF sukurtas",
    "PDF wygenerowany"
  ],
  "Кто, когда и что изменил": [
    "Kas, kada ir ką pakeitė",
    "Kto, kiedy i co zmienił"
  ],
  "Загрузка…": [
    "Įkeliama…",
    "Ładowanie…"
  ],
  "Дата и время": [
    "Data ir laikas",
    "Data i godzina"
  ],
  "Действие": [
    "Veiksmas",
    "Działanie"
  ],
  "Общие данные": [
    "Bendri duomenys",
    "Dane ogólne"
  ],
  "Подробности": [
    "Išsamiau",
    "Szczegóły"
  ],
  "Система": [
    "Sistema",
    "System"
  ],
  "До изменения": [
    "Prieš pakeitimą",
    "Przed zmianą"
  ],
  "После изменения": [
    "Po pakeitimo",
    "Po zmianie"
  ],
  "Название": [
    "Pavadinimas",
    "Nazwa"
  ],
  "Начало": [
    "Pradžia",
    "Początek"
  ],
  "Окончание": [
    "Pabaiga",
    "Koniec"
  ],
  "Статус / событие": [
    "Būsena / įvykis",
    "Status / wydarzenie"
  ],
  "Время": [
    "Laikas",
    "Godzina"
  ],
  "Рейс": [
    "Skrydis",
    "Lot"
  ],
  "Контакты": [
    "Kontaktai",
    "Kontakty"
  ],
  "Создание": [
    "Sukūrimas",
    "Utworzenie"
  ],
  "Изменение": [
    "Pakeitimas",
    "Zmiana"
  ],
  "Удаление": [
    "Pašalinimas",
    "Usunięcie"
  ],
  "Изменение периода": [
    "Laikotarpio pakeitimas",
    "Zmiana okresu"
  ],
  "Создание периода": [
    "Laikotarpio sukūrimas",
    "Utworzenie okresu"
  ],
  "Сдвиг периода": [
    "Laikotarpio perkėlimas",
    "Przesunięcie okresu"
  ],
  "Построение цикла": [
    "Ciklo sukūrimas",
    "Utworzenie cyklu"
  ],
  "Изменение события": [
    "Įvykio pakeitimas",
    "Zmiana wydarzenia"
  ],
  "Создание события": [
    "Įvykio sukūrimas",
    "Utworzenie wydarzenia"
  ],
  "Смена пароля": [
    "Slaptažodžio pakeitimas",
    "Zmiana hasła"
  ],
  "Создана демонстрация": [
    "Sukurta demonstracija",
    "Utworzono demonstrację"
  ],
  "Удалить из списка": [
    "Pašalinti iš sąrašo",
    "Usuń z listy"
  ],
  "Вернуть в список": [
    "Grąžinti į sąrašą",
    "Przywróć do listy"
  ],
  "Сделать работника неактивным?": [
    "Padaryti darbuotoją neaktyvų?",
    "Ustawić pracownika jako nieaktywnego?"
  ],
  "Работник исчезнет из активного списка. Его назначения, ротации и история сохранятся. Его можно вернуть через фильтр «Неактивные работники».": [
    "Darbuotojas bus paslėptas aktyviame sąraše. Jo priskyrimai, rotacijos ir istorija bus išsaugoti. Jį galima grąžinti naudojant filtrą „Neaktyvūs darbuotojai“.",
    "Pracownik zniknie z listy aktywnych. Jego przydziały, rotacje i historia zostaną zachowane. Można go przywrócić przez filtr „Nieaktywni pracownicy”."
  ],
  "Статус добавлен": [
    "Būsena pridėta",
    "Status dodany"
  ],
  "Событие добавлено": [
    "Įvykis pridėtas",
    "Wydarzenie dodane"
  ],
  "Слой": [
    "Sluoksnis",
    "Warstwa"
  ],
  "Выберите день в строке работника": [
    "Pasirinkite dieną darbuotojo eilutėje",
    "Wybierz dzień w wierszu pracownika"
  ],
  "Закрыть и обновить данные": [
    "Uždaryti ir atnaujinti duomenis",
    "Zamknij i odśwież dane"
  ],
  "Не удалось подключиться к серверу.": [
    "Nepavyko prisijungti prie serverio.",
    "Nie udało się połączyć z serwerem."
  ],
  "Сервер недоступен.": [
    "Serveris nepasiekiamas.",
    "Serwer jest niedostępny."
  ],
  "Войдите в систему.": [
    "Prisijunkite prie sistemos.",
    "Zaloguj się."
  ],
  "Нет доступа к проекту.": [
    "Nėra prieigos prie projekto.",
    "Brak dostępu do projektu."
  ],
  "Доступно только администратору.": [
    "Prieinama tik administratoriui.",
    "Dostępne tylko dla administratora."
  ],
  "Неверный логин или пароль.": [
    "Neteisingas prisijungimo vardas arba slaptažodis.",
    "Nieprawidłowy login lub hasło."
  ],
  "Текущий пароль неверен.": [
    "Dabartinis slaptažodis neteisingas.",
    "Obecne hasło jest nieprawidłowe."
  ],
  "Проект архивирован. Сначала восстановите его.": [
    "Projektas archyvuotas. Pirmiausia jį atkurkite.",
    "Projekt jest zarchiwizowany. Najpierw go przywróć."
  ],
  "Работник архивирован. Сначала восстановите его.": [
    "Darbuotojas neaktyvus. Pirmiausia jį atkurkite.",
    "Pracownik jest nieaktywny. Najpierw go przywróć."
  ],
  "Запись уже изменена другим пользователем. Обновите данные и повторите правку.": [
    "Įrašą jau pakeitė kitas naudotojas. Atnaujinkite duomenis ir pakartokite pakeitimą.",
    "Inny użytkownik zmienił już rekord. Odśwież dane i ponów zmianę."
  ],
  "Период выходит за даты назначения работника на проект.": [
    "Laikotarpis nepatenka į darbuotojo priskyrimo projektui datas.",
    "Okres wykracza poza daty przydziału pracownika do projektu."
  ],
  "Периоды пересекаются на одном слое или относятся к разным проектам.": [
    "Laikotarpiai persidengia tame pačiame sluoksnyje arba priklauso skirtingiems projektams.",
    "Okresy nakładają się na tej samej warstwie lub należą do różnych projektów."
  ],
  "Дата окончания должна быть не раньше даты начала.": [
    "Pabaigos data negali būti ankstesnė už pradžios datą.",
    "Data końca nie może być wcześniejsza od daty początku."
  ],
  "Работник не назначен на проект.": [
    "Darbuotojas nepriskirtas projektui.",
    "Pracownik nie jest przydzielony do projektu."
  ],
  "Событие выходит за даты назначения.": [
    "Įvykis nepatenka į priskyrimo datas.",
    "Wydarzenie wykracza poza daty przydziału."
  ],
  "Сначала назначьте работников на проект.": [
    "Pirmiausia priskirkite darbuotojus projektui.",
    "Najpierw przydziel pracowników do projektu."
  ],
  "Сначала восстановите проект.": [
    "Pirmiausia atkurkite projektą.",
    "Najpierw przywróć projekt."
  ],
  "Нужен активный проект и активный работник.": [
    "Reikalingas aktyvus projektas ir aktyvus darbuotojas.",
    "Potrzebny jest aktywny projekt i aktywny pracownik."
  ],
  "планирование команды": [
    "komandos planavimas",
    "planowanie zespołu"
  ],
  "Запись не найдена.": [
    "Įrašas nerastas.",
    "Nie znaleziono rekordu."
  ],
  "Слишком много попыток. Повторите через 15 минут.": [
    "Per daug bandymų. Bandykite po 15 minučių.",
    "Zbyt wiele prób. Spróbuj za 15 minut."
  ],
  "Сначала просмотрите изменения графика. Предпросмотр устарел.": [
    "Pirmiausia peržiūrėkite grafiko pakeitimus. Peržiūra paseno.",
    "Najpierw sprawdź zmiany grafiku. Podgląd jest nieaktualny."
  ],
  "Время указывается в формате ЧЧ:ММ.": [
    "Laikas nurodomas formatu VV:MM.",
    "Godzinę podaj w formacie GG:MM."
  ],
  "Удаление недоступно. Используйте архивирование.": [
    "Pašalinimas negalimas. Naudokite archyvavimą.",
    "Usuwanie niedostępne. Użyj archiwizacji."
  ],
  "Неизвестный часовой пояс. Пример: Europe/Stockholm.": [
    "Nežinoma laiko juosta. Pavyzdys: Europe/Stockholm.",
    "Nieznana strefa czasowa. Przykład: Europe/Stockholm."
  ],
  "Для сдвига следующих периодов сохраните длительность выбранного периода.": [
    "Norėdami perkelti vėlesnius laikotarpius, nekeiskite pasirinkto laikotarpio trukmės.",
    "Aby przesunąć kolejne okresy, zachowaj długość wybranego okresu."
  ],
  "Даты проекта должны охватывать все назначения.": [
    "Projekto datos turi apimti visus priskyrimus.",
    "Daty projektu muszą obejmować wszystkie przydziały."
  ],
  "Назначайте активных руководителей проектов.": [
    "Priskirkite aktyvius projektų vadovus.",
    "Przydzielaj aktywnych kierowników projektów."
  ],
  "Смена объекта создаст конфликт назначений.": [
    "Objekto pakeitimas sukels priskyrimų konfliktą.",
    "Zmiana obiektu spowoduje konflikt przydziałów."
  ],
  "Логин: 3–64 латинских символа, цифры, точка, дефис или подчёркивание.": [
    "Prisijungimo vardas: 3–64 lotyniškos raidės, skaitmenys, taškas, brūkšnelis arba pabraukimas.",
    "Login: 3–64 litery łacińskie, cyfry, kropka, myślnik lub podkreślenie."
  ],
  "Нельзя отключить собственную учётную запись.": [
    "Negalite išjungti savo paskyros.",
    "Nie można wyłączyć własnego konta."
  ],
  "Сначала восстановите проект и работника.": [
    "Pirmiausia atkurkite projektą ir darbuotoją.",
    "Najpierw przywróć projekt i pracownika."
  ],
  "Назначение выходит за даты проекта.": [
    "Priskyrimas nepatenka į projekto datas.",
    "Przydział wykracza poza daty projektu."
  ],
  "У назначения нельзя менять проект или работника. Создайте новое назначение.": [
    "Priskyrimo projekto ar darbuotojo pakeisti negalima. Sukurkite naują priskyrimą.",
    "Nie można zmienić projektu ani pracownika przydziału. Utwórz nowy przydział."
  ],
  "Назначение пересекается с существующим назначением на этот проект или другой объект.": [
    "Priskyrimas persidengia su esamu priskyrimu šiam projektui ar kitam objektui.",
    "Przydział nakłada się na istniejący przydział do tego projektu lub innego obiektu."
  ],
  "Даты назначения должны охватывать события работника.": [
    "Priskyrimo datos turi apimti darbuotojo įvykius.",
    "Daty przydziału muszą obejmować wydarzenia pracownika."
  ],
  "Допускается не более 32 слоёв графика.": [
    "Leidžiama ne daugiau kaip 32 grafiko sluoksniai.",
    "Dozwolone są maksymalnie 32 warstwy grafiku."
  ],
  "Диапазон не должен превышать пять лет.": [
    "Laikotarpis negali viršyti penkerių metų.",
    "Zakres nie może przekraczać pięciu lat."
  ],
  "Длительность работы и отдыха: от 1 до 52 недель.": [
    "Darbo ir poilsio trukmė: nuo 1 iki 52 savaičių.",
    "Czas pracy i odpoczynku: od 1 do 52 tygodni."
  ],
  "Количество повторений: от 1 до 100.": [
    "Kartojimų skaičius: nuo 1 iki 100.",
    "Liczba powtórzeń: od 1 do 100."
  ],
  "Укажите дату окончания или количество повторений.": [
    "Nurodykite pabaigos datą arba kartojimų skaičių.",
    "Podaj datę końca lub liczbę powtórzeń."
  ],
  "Укажите корректную дату в формате ГГГГ-ММ-ДД.": [
    "Nurodykite teisingą datą formatu MMMM-MM-DD.",
    "Podaj poprawną datę w formacie RRRR-MM-DD."
  ],
  "Недели и количество повторений должны быть целыми числами.": [
    "Savaičių ir kartojimų skaičiai turi būti sveikieji.",
    "Liczba tygodni i powtórzeń musi być całkowita."
  ],
  "Пароль должен содержать от 10 до 256 символов.": [
    "Slaptažodis turi būti nuo 10 iki 256 simbolių.",
    "Hasło musi mieć od 10 do 256 znaków."
  ],
  "Сессия устарела. Обновите страницу.": [
    "Sesija paseno. Atnaujinkite puslapį.",
    "Sesja wygasła. Odśwież stronę."
  ],
  "Источник запроса не разрешён.": [
    "Užklausos šaltinis neleidžiamas.",
    "Źródło żądania jest niedozwolone."
  ],
  "Выберите A4 или A3.": [
    "Pasirinkite A4 arba A3.",
    "Wybierz A4 lub A3."
  ],
  "Нет работников с назначением в выбранном диапазоне.": [
    "Pasirinktame laikotarpyje nėra priskirtų darbuotojų.",
    "Brak przydzielonych pracowników w wybranym zakresie."
  ],
  "Выберите хотя бы одного работника.": [
    "Pasirinkite bent vieną darbuotoją.",
    "Wybierz co najmniej jednego pracownika."
  ],
  "Нет доступа к выбранным работникам в этом диапазоне.": [
    "Nėra prieigos prie pasirinktų darbuotojų šiame laikotarpyje.",
    "Brak dostępu do wybranych pracowników w tym zakresie."
  ],
  "Не удалось выполнить запрос. Повторите попытку; подробности записаны в журнале сервера.": [
    "Nepavyko įvykdyti užklausos. Bandykite dar kartą; išsami informacija įrašyta serverio žurnale.",
    "Nie udało się wykonać żądania. Spróbuj ponownie; szczegóły zapisano w dzienniku serwera."
  ],
  "Такая запись уже существует или связанная запись недоступна.": [
    "Toks įrašas jau yra arba susijęs įrašas neprieinamas.",
    "Taki rekord już istnieje lub powiązany rekord jest niedostępny."
  ],
  "Не удалось сохранить.": [
    "Nepavyko išsaugoti.",
    "Nie udało się zapisać."
  ],
  "Здесь создаётся период на один день. Нажмите на полосу, чтобы изменить даты.": [
    "Čia sukuriamas vienos dienos laikotarpis. Spustelėkite juostą, kad pakeistumėte datas.",
    "Tutaj powstaje okres na jeden dzień. Kliknij pasek, aby zmienić daty."
  ],
  "Секретарь": [
    "Sekretorius",
    "Sekretarz"
  ],
  "Зарегистрировать работника": [
    "Registruoti darbuotoją",
    "Zarejestruj pracownika"
  ],
  "Зарегистрировать": [
    "Registruoti",
    "Zarejestruj"
  ],
  "Сразу назначить на проект": [
    "Iškart priskirti projektui",
    "Od razu przydziel do projektu"
  ],
  "Без назначения": [
    "Be priskyrimo",
    "Bez przydziału"
  ],
  "Добавить период": [
    "Pridėti laikotarpį",
    "Dodaj okres"
  ],
  "Добавить пользователя": [
    "Pridėti naudotoją",
    "Dodaj użytkownika"
  ],
  "Новый пользователь": [
    "Naujas naudotojas",
    "Nowy użytkownik"
  ],
  "Доступ руководителей и секретарей к проектам": [
    "Vadovų ir sekretorių prieiga prie projektų",
    "Dostęp kierowników i sekretarzy do projektów"
  ],
  "Руководители и секретари": [
    "Vadovai ir sekretoriai",
    "Kierownicy i sekretarze"
  ],
  "Просмотр периода": [
    "Laikotarpio peržiūra",
    "Podgląd okresu"
  ],
  "Просмотр события": [
    "Įvykio peržiūra",
    "Podgląd wydarzenia"
  ],
  "Секретарь может изменять только работу и больничные.": [
    "Sekretorius gali keisti tik darbo ir nedarbingumo laikotarpius.",
    "Sekretarz może zmieniać tylko pracę i zwolnienia lekarskie."
  ],
  "Секретарь может изменять только работу и больничные, по одному периоду.": [
    "Sekretorius gali keisti tik darbo ir nedarbingumo laikotarpius, po vieną.",
    "Sekretarz może zmieniać tylko pracę i zwolnienia lekarskie, po jednym okresie."
  ],
  "Секретарь может изменять только работу, больничные и перелёты.": [
    "Sekretorius gali keisti tik darbą, nedarbingumą ir skrydžius.",
    "Sekretarz może zmieniać tylko pracę, zwolnienia lekarskie i loty."
  ],
  "Секретарь может изменять только перелёты.": [
    "Sekretorius gali keisti tik skrydžius.",
    "Sekretarz może zmieniać tylko loty."
  ],
  "Построение циклов доступно администратору и руководителю.": [
    "Ciklus kurti gali administratorius ir vadovas.",
    "Cykle mogą tworzyć administrator i kierownik."
  ],
  "Назначайте активных руководителей или секретарей.": [
    "Priskirkite aktyvius vadovus arba sekretorius.",
    "Przydzielaj aktywnych kierowników lub sekretarzy."
  ],
  "Выберите роль руководителя или секретаря.": [
    "Pasirinkite vadovo arba sekretoriaus vaidmenį.",
    "Wybierz rolę kierownika lub sekretarza."
  ],
  "Роль администратора нельзя изменить.": [
    "Administratoriaus vaidmens keisti negalima.",
    "Nie można zmienić roli administratora."
  ],
  "Команда": [
    "Komanda",
    "Zespół"
  ],
  "По командам": [
    "Pagal komandas",
    "Według zespołów"
  ],
  "Без команды": [
    "Be komandos",
    "Bez zespołu"
  ],
  "Команда работника": [
    "Darbuotojo komanda",
    "Zespół pracownika"
  ],
  "Новая команда": [
    "Nauja komanda",
    "Nowy zespół"
  ],
  "Изменить команду": [
    "Keisti komandą",
    "Edytuj zespół"
  ],
  "Название команды": [
    "Komandos pavadinimas",
    "Nazwa zespołu"
  ],
  "Работники команды": [
    "Komandos darbuotojai",
    "Pracownicy zespołu"
  ],
  "В команде пока нет работников.": [
    "Komandoje dar nėra darbuotojų.",
    "W zespole nie ma jeszcze pracowników."
  ],
  "У работника одна команда в каждом проекте. При выборе работника из другой команды он будет перенесён в эту команду.": [
    "Darbuotojas kiekviename projekte priklauso vienai komandai. Pasirinkus darbuotoją iš kitos komandos, jis bus perkeltas į šią komandą.",
    "Pracownik należy do jednego zespołu w każdym projekcie. Wybranie pracownika z innego zespołu przeniesie go do tego zespołu."
  ],
  "Сначала создайте активный проект.": [
    "Pirmiausia sukurkite aktyvų projektą.",
    "Najpierw utwórz aktywny projekt."
  ],
  "Команда относится к другому проекту.": [
    "Komanda priklauso kitam projektui.",
    "Zespół należy do innego projektu."
  ],
  "Назначение команды изменилось. Обновите данные.": [
    "Komandos priskyrimas pasikeitė. Atnaujinkite duomenis.",
    "Przydział do zespołu się zmienił. Odśwież dane."
  ],
  "Некорректный список работников команды.": [
    "Neteisingas komandos darbuotojų sąrašas.",
    "Nieprawidłowa lista pracowników zespołu."
  ],
  "Выберите работников команды.": [
    "Pasirinkite komandos darbuotojus.",
    "Wybierz pracowników zespołu."
  ],
  "Некорректное назначение работника.": [
    "Neteisingas darbuotojo priskyrimas.",
    "Nieprawidłowy przydział pracownika."
  ],
  "Назначение команды": [
    "Komandos priskyrimas",
    "Przydział do zespołu"
  ],
  "Создание команды": [
    "Komandos sukūrimas",
    "Utworzenie zespołu"
  ],
  "Изменение команды": [
    "Komandos pakeitimas",
    "Zmiana zespołu"
  ],
  "Создать учётную запись": [
    "Sukurti paskyrą",
    "Utwórz konto"
  ],
  "Учётные записи создаются только для руководителей проектов и секретарей. Работники не имеют доступа к системе.": [
    "Paskyros kuriamos tik projektų vadovams ir sekretoriams. Darbuotojai neturi prieigos prie sistemos.",
    "Konta tworzy się tylko dla kierowników projektów i sekretarzy. Pracownicy nie mają dostępu do systemu."
  ],
  "Добавить в команду": [
    "Pridėti į komandą",
    "Dodaj do zespołu"
  ],
  "Удалить команду": [
    "Pašalinti komandą",
    "Usuń zespół"
  ],
  "Удалить команду, оставить работников на объекте": [
    "Pašalinti komandą, palikti darbuotojus objekte",
    "Usuń zespół, pozostaw pracowników na obiekcie"
  ],
  "Удалить команду и убрать работников из проекта": [
    "Pašalinti komandą ir darbuotojų priskyrimus projektui",
    "Usuń zespół i przydziały pracowników do projektu"
  ],
  "Карточки работников и история сохранятся при любом варианте.": [
    "Darbuotojų kortelės ir istorija išsaugomos abiem atvejais.",
    "Karty pracowników i historia zostaną zachowane w obu wariantach."
  ],
  "Что сделать с работниками": [
    "Ką daryti su darbuotojais",
    "Co zrobić z pracownikami"
  ],
  "Назначение работника на этот проект неактивно.": [
    "Darbuotojo priskyrimas šiam projektui neaktyvus.",
    "Przydział pracownika do tego projektu jest nieaktywny."
  ],
  "Назначение активно": [
    "Priskyrimas aktyvus",
    "Przydział aktywny"
  ],
  "Неактивное назначение": [
    "Neaktyvus priskyrimas",
    "Nieaktywny przydział"
  ],
  "Отключение назначения": [
    "Priskyrimo išjungimas",
    "Wyłączenie przydziału"
  ],
  "Удаление команды": [
    "Komandos pašalinimas",
    "Usunięcie zespołu"
  ],
  "Команда удалена.": [
    "Komanda pašalinta.",
    "Zespół usunięty."
  ],
  "Команда уже удалена.": [
    "Komanda jau pašalinta.",
    "Zespół został już usunięty."
  ],
  "Выберите способ удаления команды.": [
    "Pasirinkite komandos pašalinimo būdą.",
    "Wybierz sposób usunięcia zespołu."
  ],
  "На объекте по дням": [
    "Objekte kiekvieną dieną",
    "Na obiekcie każdego dnia"
  ],
  "На объекте": [
    "Objekte",
    "Na obiekcie"
  ],
  "Роль работника": [
    "Darbuotojo vaidmuo",
    "Rola pracownika"
  ],
  "Неизвестная роль работника.": [
    "Nežinomas darbuotojo vaidmuo.",
    "Nieznana rola pracownika."
  ],
  "Светлая тема": [
    "Šviesi tema",
    "Jasny motyw"
  ],
  "Тёмная тема": [
    "Tamsi tema",
    "Ciemny motyw"
  ],
  "Добавить работника в проект": [
    "Pridėti darbuotoją į projektą",
    "Dodaj pracownika do projektu"
  ],
  "Выбрать из списка работников": [
    "Pasirinkti iš darbuotojų sąrašo",
    "Wybierz z listy pracowników"
  ],
  "Создать карточку работника": [
    "Sukurti darbuotojo kortelę",
    "Utwórz kartę pracownika"
  ]
};
const translationKeys=Object.keys(UI_TRANSLATIONS).sort((a,b)=>b.length-a.length);
const translationPatterns=translationKeys.map(key=>{const escaped=key.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');return [key,new RegExp('(?<![\\p{L}])'+escaped+'(?![\\p{L}])','gu')]});
function translateText(value){
 if(language==='ru'||!/[А-Яа-яЁё]/.test(value))return value;
 const index=language==='lt'?0:1;
 let protectedValues=[];
 if(typeof state!=='undefined'&&state){for(const entity of [...state.projects,...state.employees,...state.sites,...state.users,...state.events,...(state.teams||[])])for(const [key,v] of Object.entries(entity))if(['name','first_name','last_name','specialty','contact','notes','city','country','address','site_name','route','flight','username'].includes(key)&&typeof v==='string'&&v)protectedValues.push(v);for(const employee of state.employees)protectedValues.push(employee.first_name+' '+employee.last_name)}
 protectedValues=[...new Set(protectedValues)].sort((a,b)=>b.length-a.length);
 let markers=[];let result=value;
 for(const v of protectedValues){if(result.includes(v)){const marker='\uE000'+markers.length+'\uE001';result=result.split(v).join(marker);markers.push(v)}}
 for(const [key,pattern] of translationPatterns)result=result.replace(pattern,()=>UI_TRANSLATIONS[key][index]);
 return result.replace(/\uE000(\d+)\uE001/g,(_,n)=>markers[Number(n)]);
}
function languageSelect(){return `<select class="language-select" data-language aria-label="Language">${LANGUAGE_OPTIONS.map(([code,label])=>`<option value="${code}" ${code===language?'selected':''}>${label}</option>`).join('')}</select>`}
function translateUI(root=document.body){
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let node;
 while((node=walker.nextNode())){if(['SCRIPT','STYLE','TEXTAREA'].includes(node.parentElement?.tagName))continue;let next=translateText(node.nodeValue);if(next!==node.nodeValue)node.nodeValue=next}
 for(const el of root.querySelectorAll('[title],[placeholder],[aria-label]'))for(const attr of ['title','placeholder','aria-label'])if(el.hasAttribute(attr)){let v=el.getAttribute(attr),next=translateText(v);if(v!==next)el.setAttribute(attr,next)}
 document.documentElement.lang=language;
 document.title=translateText('Ротации — планирование команды');
}
document.addEventListener('change',event=>{if(!event.target.matches('[data-language]'))return;language=event.target.value;localStorage.setItem('rotations-language',language);closeModal();render();translateUI()});
new MutationObserver(()=>translateUI()).observe(document.body,{childList:true,subtree:true,characterData:true});
