# IOB Calculator

A simple Python script to calculate **Insulin On Board (IOB)** from bolus history.

## Features
- Accepts doses with elapsed time or clock time (`hh:mm`).
- Supports multiple boluses in one call.
- Configurable DIA (Duration of Insulin Action).
- Optional peak switch for alternate absorption models.
- Command-line interface (CLI) ready.

## Usage

```bash
python iob.py U, Elapsed_time
python iob.py U, Elapsed_time, U, Elapsed_time, ...
python iob.py U,"hh:mm"
python iob.py U,"hh:mm", U,"hh:mm", U,"hh:mm" ...

### Options
--dia <hours>` : Set custom duration of insulin action.
--peak <minutes>` : Adjust absorption peak.

```

## Examples

```bash
# Single bolus, elapsed time
python iob.py 1.0 120

# Multiple boluses, elapsed times
python iob.py 1.0 120 2.0 60 0.8 30

# Using clock time
python iob.py 1.0 "22:30" 2.0 "23:00" 0.8 "01:10"

# With custom DIA (6 hours)
python iob.py 1.0 "23:00" --dia 6

# With custom peak (90 minutes)
python iob.py 1.0 "23:00" --peak 90

```

## License
MIT License. See [LICENSE](LICENSE) for details.

## Disclaimer
This software is provided for educational and informational purposes only.  
It must **not** be used to make medical decisions without consulting your own physician or a qualified healthcare provider.  
The authors and contributors accept no responsibility for any consequences resulting from the use of this software in medical or clinical settings.
