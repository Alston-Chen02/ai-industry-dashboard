import importlib.util,json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('refresh',Path(__file__).resolve().parents[1]/'scripts/refresh_news.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
NOW=datetime(2026,11,1,1,tzinfo=timezone.utc)
URL='https://openai.com/index/test-announcement'
def page(stamp='2026-11-01T00:30:00Z'):
 return '<meta property="article:published_time" content="'+stamp+'">'
def article(url=URL,event='new-event'):
 return dict(url=url,event_key=event,vendor='OpenAI',topic=m.TOPICS[0],title='測試公告',summary='測試用摘要',why='用於驗證資料處理',source='測試來源')
def old():
 return {'edition':'2026-10-31','reviewedAt':'2026-10-31','editions':[],'articles':[{'id':'preserved-bookmark-id','url':URL,'status':'歷史公告'}]}
class RefreshTests(unittest.TestCase):
 def test_search_sources_and_inline_citations(self):
  response={'output':[{'type':'web_search_call','action':{'sources':[{'url':URL},{'url':'https://untrusted.example/article'}]}},{'type':'message','content':[{'type':'output_text','text':'research','annotations':[{'type':'url_citation','url':'https://www.anthropic.com/news/test'}]}]}]}
  self.assertEqual(m.source_urls(response),{URL,'https://www.anthropic.com/news/test'})
 def test_timezone_qualified_metadata(self):
  self.assertEqual(m.original_timestamp(page('2026-11-01T08:30:00+08:00')),datetime(2026,11,1,0,30,tzinfo=timezone.utc))
 def test_date_only_is_not_exact_time(self):
  with self.assertRaises(m.RefreshError):m.original_timestamp(page('2026-11-01'))
 def test_conflicting_original_timestamps_rejected(self):
  with self.assertRaises(m.RefreshError):m.original_timestamp(page()+page('2026-10-30T00:00:00Z'))
 def test_jsonld_only_article_publication(self):
  html='<script type="application/ld+json">'+json.dumps({'@graph':[{'@type':'Organization','datePublished':'2020-01-01T00:00:00Z'},{'@type':'NewsArticle','datePublished':'2026-11-01T00:30:00Z'}]})+'</script>'
  self.assertEqual(m.original_timestamp(html),datetime(2026,11,1,0,30,tzinfo=timezone.utc))
 def test_old_and_future_news_excluded(self):
  for stamp in ('2026-10-30T00:00:00Z','2026-11-01T02:00:00Z'):
   accepted,rejected=m.validate_candidates([article()],{URL},NOW,lambda u:(u,page(stamp)))
   self.assertEqual(accepted,[]);self.assertEqual(len(rejected),1)
 def test_summary_limit(self):
  a=article();a['summary']='文'*51
  accepted,rejected=m.validate_candidates([a],{URL},NOW,lambda u:(u,page()))
  self.assertFalse(accepted);self.assertTrue(rejected)
 def test_source_must_be_in_search_results(self):
  accepted,rejected=m.validate_candidates([article()],set(),NOW,lambda u:(u,page()))
  self.assertFalse(accepted);self.assertTrue(rejected)
 def test_tracking_and_untrusted_domains(self):
  self.assertEqual(m.clean_url(URL+'?utm_source=x#section'),URL)
  for u in ('http://openai.com/news','https://openai.com.attacker.example/news','https://user:pass@openai.com/news','https://127.0.0.1/news','https://openai.com:444/news'):
   with self.assertRaises(m.RefreshError):m.clean_url(u)
 def test_duplicate_event_and_redirect(self):
  u2='https://openai.com/index/second'
  accepted,rejected=m.validate_candidates([article(),article(u2,'another')],{URL,u2},NOW,lambda u:(URL,page()))
  self.assertEqual(len(accepted),1);self.assertEqual(len(rejected),1)
 def test_bookmark_identity_and_archive(self):
  accepted,_=m.validate_candidates([article()],{URL},NOW,lambda u:(u,page()))
  d=m.apply_edition(old(),accepted,NOW,'tested')
  self.assertEqual(d['articles'][0]['id'],'preserved-bookmark-id')
  self.assertEqual(d['editions'][0]['articleIds'],['preserved-bookmark-id'])
  self.assertEqual(d['edition'],'2026-11-01')
 def test_quiet_day_is_preserved_as_an_edition(self):
  d=m.apply_edition(old(),[],NOW,'tested')
  self.assertEqual(d['editions'][0]['status'],'quiet');self.assertEqual(d['editions'][0]['articleIds'],[])
 def test_missing_key_keeps_previous_data(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)),patch.dict('os.environ',{'OPENAI_API_KEY':''}):
   p=Path(tmp)/'data.json';p.write_text(json.dumps(old()));before=p.read_bytes();self.assertEqual(m.main(),0)
   self.assertEqual(p.read_bytes(),before);self.assertEqual(json.loads((Path(tmp)/'refresh-status.json').read_text())['state'],'needs_key')
 def test_unavailable_index_reports_limited_coverage_without_fabricated_news(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)),patch.dict('os.environ',{'OPENAI_API_KEY':'unit-test-placeholder'}),patch.object(m,'discover',return_value=({'articles':[]},{URL})),patch.object(m,'get_page',side_effect=m.RefreshError('Source unavailable')):
   (Path(tmp)/'data.json').write_text(json.dumps(old()))
   m.main();d=json.loads((Path(tmp)/'data.json').read_text())
   self.assertTrue(d['coverageLimited']);self.assertIn('0/3',d['coverage']);self.assertEqual(d['editions'][0]['articleIds'],[])
   self.assertEqual(d['articles'][0]['id'],'preserved-bookmark-id')
 def test_api_failure_retains_data_and_success_time(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)),patch.dict('os.environ',{'OPENAI_API_KEY':'unit-test-placeholder'}),patch.object(m,'discover',side_effect=m.RefreshError('API unavailable')):
   p=Path(tmp)/'data.json';p.write_text(json.dumps(old()));before=p.read_bytes()
   (Path(tmp)/'refresh-status.json').write_text(json.dumps({'lastSuccessAt':'2026-10-31T00:00:00Z'}))
   m.main();self.assertEqual(p.read_bytes(),before)
   s=json.loads((Path(tmp)/'refresh-status.json').read_text());self.assertEqual(s['state'],'failed');self.assertEqual(s['lastSuccessAt'],'2026-10-31T00:00:00Z')
if __name__=='__main__':unittest.main()
