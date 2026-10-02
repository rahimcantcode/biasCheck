"""Render the standalone v2 reviewer without changing archived v1 artifacts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def render():
    template = (ROOT / 'reviewer.template.html').read_text()
    payload = (ROOT / 'pilot_manifest_v2.json').read_text().replace('<', '\\u003c')
    script = (ROOT / 'reviewer.js').read_text().replace('</script', '<\\/script')
    result = template.replace('__PILOT_DATA__', payload).replace('__REVIEWER_SCRIPT__', script)
    (ROOT / 'Bias_Checker_Review_Pilot.html').write_text(result)
    return result


if __name__ == '__main__':
    render()
