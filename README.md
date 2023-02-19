# FJNU-ics

Generate ics from DLMU system.  

## Installation

```sh
git clone https://github.com/MoveToEx/DLMU-ics
cd DLMU-ics
pip install -r requirements.txt
```

## Usage

Before running Python, open your browser and login to [DLMU](http://jw.xpaas.dlmu.edu.cn/eams/homeExt.action).  
Then run the script in the following format:

```sh
python main.py -d YYYY/MM/DD
```

where YYYY/MM/DD specifies the first Monday of the current semester.  

After the script prints `Success` on the console, find `output.ics` in the repo directory.  

## Disclaimer

As the complete login process of DLMU system is still unclear, this program uses cookies from the previous login session to fetch data.  
We promise that your cookies will not be used anywhere apart from generating this ics file.  
Besides, it's unknown whether we have fully implemented every function of DLMU system, so be cautious in case it outputs faulty ics file.
Using this program means that you have understood possible consequences.

## To-Do

- [ ] Full geo location support
- [ ] Auto date alignment
