\# IOB Calculator



A simple Python script to calculate \*\*Insulin On Board (IOB)\*\* from bolus history.



\## Features

\- Accepts doses with elapsed time or clock time (`hh:mm`).

\- Supports multiple boluses in one call.

\- Configurable DIA (Duration of Insulin Action).

\- Optional peak switch for alternate absorption models.

\- Command-line interface (CLI) ready.



\## Usage



```bash

python iob.py IOB U, Elapsed\_time

python iob.py IOB U, Elapsed\_time, U, Elapsed\_time, ...

python iob.py IOB U,"hh:mm"

python iob.py IOB U,"hh:mm", U,"hh:mm", U,"hh:mm" ...

Options

--dia <hours> : Set custom duration of insulin action.



--peak <hours> : Adjust absorption peak.



Examples

bash

Copy code

\# Single bolus, elapsed time

python iob.py 1.0 120



\# Multiple boluses, elapsed times

python iob.py 1.0 120 2.0 60 0.8 30



\# Using clock time

python iob.py 1.0 "22:30" 2.0 "23:00" 0.8 "01:10"



\# With custom DIA

python iob.py 1.0 "23:00" --dia 6



License

MIT License. See LICENSE for details.

