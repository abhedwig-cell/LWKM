from types import SimpleNamespace
from tools.execute_swap_candidate import execute


def test_zero_exit_without_completion_is_failure(tmp_path,monkeypatch):
    src=tmp_path/'in';src.mkdir();(src/'swap.swp').write_text('test')
    binary=tmp_path/'binary';binary.write_bytes(b'fixture')
    monkeypatch.setattr('tools.execute_swap_candidate.subprocess.run',
                        lambda *a,**k:SimpleNamespace(returncode=0,stdout=b'Fatal execution error'))
    r=execute(binary,src,tmp_path/'run')
    assert r['status']=='EXECUTION_FAIL'


def test_swap431_success_code_100_requires_valid_output(tmp_path,monkeypatch):
    src=tmp_path/'in';src.mkdir();(src/'swap.swp').write_text('test')
    binary=tmp_path/'binary';binary.write_bytes(b'fixture')
    def run(*a,**k):
        (k['cwd']/'result_output.csv').write_text('* metadata\nDATE,GWL\n1971-01-01,-12.5\n1971-01-02,-13.0\n')
        return SimpleNamespace(returncode=100,stdout=b'Swap normal completion!')
    monkeypatch.setattr('tools.execute_swap_candidate.subprocess.run',run)
    r=execute(binary,src,tmp_path/'run')
    assert r['status']=='EXECUTION_PASS' and r['output_rows']==2


def test_normal_completion_with_output_gap_is_failure(tmp_path,monkeypatch):
    src=tmp_path/'in';src.mkdir();(src/'swap.swp').write_text('test')
    binary=tmp_path/'binary';binary.write_bytes(b'fixture')
    def run(*a,**k):
        (k['cwd']/'result_output.csv').write_text('DATE,GWL\n1971-01-01,-12.5\n1971-01-03,-13.0\n')
        return SimpleNamespace(returncode=100,stdout=b'Swap normal completion!')
    monkeypatch.setattr('tools.execute_swap_candidate.subprocess.run',run)
    assert execute(binary,src,tmp_path/'run')['status']=='EXECUTION_FAIL'
