from pathlib import Path
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    template=(ROOT/'reviewer.template.html').read_text()
    payload=(ROOT/'pilot_manifest.json').read_text().replace('<','\\u003c')
    (ROOT/'Bias_Checker_Review_Pilot.html').write_text(template.replace('__PILOT_DATA__',payload))
