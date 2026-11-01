import importlib.util,json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
import io,urllib.error
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
 def test_http_redirect_keeps_canonical_trailing_slash(self):
  seen=[]
  class Response:
   headers={'Content-Type':'text/html'}
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def read(self,n):return page().encode()
  class Opener:
   def open(self,request,timeout):
    seen.append(request.full_url)
    if len(seen)==1:raise urllib.error.HTTPError(request.full_url,301,'moved',{'Location':'/news/'},io.BytesIO())
    return Response()
  with patch.object(m.urllib.request,'build_opener',return_value=Opener()),patch.object(m,'public_host'):
   final,html=m.get_page('https://openai.com/news')
  self.assertEqual(seen,['https://openai.com/news','https://openai.com/news/']);self.assertEqual(final,seen[-1])
 def test_publisher_rss_requires_timestamp_and_same_publisher_link(self):
  xml='<rss><channel><item><title>Original news</title><link>'+URL+'</link><pubDate>Sun, 01 Nov 2026 00:30:00 GMT</pubDate><description>Publisher summary</description></item><item><link>https://www.anthropic.com/news/other</link><pubDate>Sun, 01 Nov 2026 00:30:00 GMT</pubDate></item><item><link>'+URL+'</link><pubDate>2026-11-01</pubDate></item></channel></rss>'
  entries=m.parse_official_feed(xml,m.FEEDS[0])
  self.assertEqual(len(entries),1);self.assertEqual(entries[0][0],URL);self.assertEqual(m.original_timestamp(entries[0][1]),datetime(2026,11,1,0,30,tzinfo=timezone.utc))
 def test_rss_old_news_can_establish_empty_edition_when_article_pages_unavailable(self):
  research={'status':'completed','output':[{'type':'web_search_call','status':'completed','action':{'sources':[{'url':URL}]}}]}
  xml='<rss><channel><item><title>Older news</title><link>'+URL+'</link><pubDate>Fri, 30 Oct 2026 00:30:00 GMT</pubDate></item></channel></rss>'
  def fetch(u,**kwargs):
   if u==m.FEEDS[0]:return u,xml
   raise m.RefreshError('Source unavailable')
  with patch.object(m,'call_api',return_value=research) as api,patch.object(m,'get_page',side_effect=fetch):
   result,sources=m.discover('unit-test-placeholder',NOW)
   self.assertEqual(result['articles'],[]);self.assertEqual(result['inspection']['feeds_available'],1);self.assertEqual(result['inspection']['old'],1);self.assertEqual(api.call_count,1)
 def test_preinspection_classifies_without_inferring_missing_dates(self):
  urls={f'https://openai.com/index/case-{i}' for i in range(5)}
  def fetch(u):
   i=int(u[-1])
   if i==4:raise m.RefreshError('Source unavailable')
   stamps=['2026-11-01T00:30:00Z','2026-10-30T00:00:00Z','2026-11-01','2026-11-01T03:00:00Z']
   return u,page(stamps[i])
  eligible,pages,report=m.inspect_sources(urls,NOW,fetch)
  self.assertEqual(len(eligible),1)
  for k in ('recent','old','future','date_unverified','unavailable'):self.assertEqual(report[k],1)
  self.assertEqual(set(pages),{eligible[0]['url']})
 def test_old_verified_sources_produce_empty_edition_without_summary_call(self):
  research={'status':'completed','output':[{'type':'web_search_call','status':'completed','action':{'sources':[{'url':URL}]}}]}
  with patch.object(m,'call_api',return_value=research) as api,patch.object(m,'get_page',return_value=(URL,page('2026-10-30T00:00:00Z'))):
   result,sources=m.discover('unit-test-placeholder',NOW)
   self.assertEqual(result['articles'],[]);self.assertEqual(result['inspection']['old'],1);self.assertEqual(api.call_count,1)
 def test_unavailable_sources_fail_and_retain_previous_edition(self):
  research={'status':'completed','output':[{'type':'web_search_call','status':'completed','action':{'sources':[{'url':URL}]}}]}
  with tempfile.TemporaryDirectory() as tmp,patch.object(m,'ROOT',Path(tmp)),patch.dict('os.environ',{'OPENAI_API_KEY':'unit-test-placeholder'}),patch.object(m,'call_api',return_value=research),patch.object(m,'get_page',side_effect=m.RefreshError('Source unavailable')):
   p=Path(tmp)/'data.json';p.write_text(json.dumps(old()));before=p.read_bytes()
   m.main();self.assertEqual(p.read_bytes(),before)
   self.assertEqual(json.loads((Path(tmp)/'refresh-status.json').read_text())['state'],'failed')
 def test_summary_receives_only_preverified_recent_source_content(self):
  older='https://openai.com/index/older'
  research={'status':'completed','output':[{'type':'web_search_call','status':'completed','action':{'sources':[{'url':URL},{'url':older}]}}]}
  calls=[]
  def api(payload,key):
   calls.append(payload)
   if len(calls)==1:return research
   supplied=json.loads(payload['input'][1]['content'])['verified_source_pages']
   self.assertEqual([a['url'] for a in supplied],[URL]);self.assertIn('real article content',supplied[0]['text'])
   return {'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps({'articles':[article()],'coverage_note':'tested'})}]}]}
  def fetch(u,**kwargs):return u,page('2026-10-30T00:00:00Z' if u==older else '2026-11-01T00:30:00Z')+'<article>real article content</article>'
  with patch.object(m,'call_api',side_effect=api),patch.object(m,'get_page',side_effect=fetch):
   result,sources=m.discover('unit-test-placeholder',NOW)
   accepted,rejected=m.validate_candidates(result['articles'],sources,NOW,lambda u:result['_pages'][u])
   self.assertEqual(len(accepted),1);self.assertEqual(rejected,[])
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
