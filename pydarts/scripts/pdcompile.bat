set pyinstallerpath=pyi\pyinstaller.py
set pydartspath=c:\Users\Administrator\Downloads\pydarts_dev
set pydartsscript=%pydartspath%\pydarts.py

%PYTHONPATH% %pyinstallerpath% ^
	--paths="%pydartspath%" ^
	--add-data="%pydartspath%\locales;locales" ^
	--add-data="%pydartspath%\sounds;sounds" ^
	--add-data="%pydartspath%\images;images" ^
	--add-data="%pydartspath%\fonts;fonts" ^
	--add-data="%pydartspath%\licence;licence" ^
	--add-data="%pydartspath%\arduino;arduino" ^
	--add-data="%pydartspath%\desktop;desktop" ^
	--add-data="%pydartspath%\CREDITS;." ^
	--add-data="%pydartspath%\README;." ^
	--hidden-import="games.321_Zlip" ^
	--hidden-import="games.Cricket" ^
	--hidden-import="games.Practice" ^
	--hidden-import="games.Ho_One" ^
	--hidden-import="games.Sample_game" ^
	--hidden-import="games.Kinito" ^
	--hidden-import="games.Killer" ^
	--hidden-import="games.Kapital" ^
	--hidden-import="games.Shanghai" ^
	--icon="%pydartspath%\images\icon_black_256.ico" ^
	-y ^
	%pydartsscript%
