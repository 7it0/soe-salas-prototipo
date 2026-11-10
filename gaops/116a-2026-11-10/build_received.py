#!/usr/bin/env python3
"""Build only GAOPS 116. Source bytes must match the two received PDFs exactly."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, unquote
import argparse, csv, hashlib, html, io, json, re, shutil, unicodedata
import requests, fitz
from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak, NextPageTemplate
from reportlab.platypus.tableofcontents import TableOfContents
ROOT=Path(__file__).resolve().parent
BASE='https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/eventos-criticos/apresentacoes-das-reunioes/'
SITE='https://7it0.github.io/soe-salas-prototipo/gaops/116a-2026-11-10/'
PDF='NT_GAOPS_116_10-11-2026_PREVIA.pdf'
ANNEX='Anexo_I_GAOPS_116_10-11-2026.pdf'
NAME='José Aguiar de Lima Jr.'
HASHES={'inpe':'7d5085dbce87548a950802b2b0f6efda5063134196f61f24fa891b7949e016d3','cemaden':'e1faf0a46061e191b6c0d834b0070d1fb7a908c74b86a9405d7ee93a37661161'}
LABELS={'inpe':'INPE/INMET','cemaden':'CEMADEN'}
PAGES={'inpe':13,'cemaden':17}
FIGS={'inpe':[(3,'Precipitação e anomalias — agosto a outubro','Diagnóstico mensal e trimestral; áreas e períodos distintos.'),(4,'Novembro — parcial até 09/11','Não representa fechamento mensal.'),(5,'Evolução das anomalias na bacia','Barras sem rótulos exatos não foram convertidas em valores numéricos.'),(6,'GOES-19 — 10/11','Contexto de nebulosidade; não é acumulado de chuva.'),(8,'Previsão diária — 11 a 13/11','Título BAM e mapas MONAN: identificação divergente preservada.'),(9,'BAM subsazonal — quatro semanas','Referência 08/11; não somar com acumulados de outros horizontes.'),(11,'Climatologia NDJ','600–800 mm e 18–26 °C: faixas climatológicas, não previsões.'),(12,'Previsão em conjunto NDJ 2026/2027','Probabilidade por tercil; branco indica probabilidades iguais.')], 'cemaden':[(2,'Precipitação nos últimos 30 dias','10/10–09/11; acumulado e anomalia separados.'),(3,'Chuva no ano hidrológico','01/10–09/11; janela sobreposta à de 30 dias.'),(4,'Evolução temporal da precipitação','55,0 mm de 1 a 9/11; anotação de 11% da MLT requer esclarecimento.'),(5,'TSI-6 — outubro','Excesso em Jaguari, Funil e Santa Cecília; demais recortes normais.'),(6,'TSI-3 — outubro','Excesso hídrico nos seis recortes; índice não é volume útil.'),(7,'Situação meteorológica atual','Imagem de satélite apresentada pelo CEMADEN.'),(8,'GEFS — chuva e anomalia em 14 dias','Rodada 10/11 00 UTC; previsão, não observação.'),(9,'GEFS — acumulado na bacia','Aproximadamente 112 mm ao final de 14 dias; dispersão dos membros.'),(10,'Terceira e quarta semanas','CFS/NOAA e ECMWF; 23–29/11 e 30/11–06/12.'),(11,'MHD — vazões naturais','07/11–07/12; MLT 1991–2020. Não representa defluências programadas.'),(12,'TSI previsto — escala de seis meses','Faixa +1,27 a +1,77; extremos não individualizados por reservatório.'),(13,'GloFAS subsazonal','Título de 30 dias e painéis 16/11–21/12: datas preservadas.'),(14,'El Niño — produto reproduzido na fonte','Niño 3.4 +2,3 °C; não é probabilidade de impacto local.'),(15,'Anos análogos','Trajetórias distintas; não representam repetição determinística.'),(16,'Chuva sazonal multimodelo','NDJ; categorias e anomalias não são acumulados diários.'),(17,'GloFAS sazonal NDJ','Novembro/dezembro de 2026 e janeiro de 2027; painéis inferiores antigos preservados.')]}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).replace('\u00ad','').replace('−','-')
def obtain(out,local=None):
    session=requests.Session();session.headers['User-Agent']='SOE-publication-source-check/1.0'
    links=[];records={}
    if local is None:
        for listing in [BASE+'apresentacoes-das-reunioes',BASE]:
            try:
                r=session.get(listing,timeout=(8,20));r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
                for a in s.find_all('a',href=True):
                    text=unquote(a['href']+' '+a.get_text(' ',strip=True)).lower()
                    if any(x in text for x in ['20261110','10112026','116ª']):links.append((urljoin(listing,a['href']),text))
                if links:break
            except Exception as e:print('Listing unavailable:',type(e).__name__,flush=True)
    fallback={'inpe':['reuniao_ana_gaops_10112026.pdf/view','reuniao_ana_gaops_10112026-1.pdf/view'], 'cemaden':['apres-cemaden-paraiba-do-sul-20261110-pptx.pdf/view','apres-cemaden-paraiba-do-sul-20261110.pdf/view','apres.-cemaden-paraiba-do-sul-20261110.pptx.pdf/view']}
    for key,expected in HASHES.items():
        dest=out/'fontes'/(key+'.pdf')
        existing=(Path(local)/(key+'.pdf')) if local else ROOT/'fontes'/(key+'.pdf')
        if existing.exists() and sha(existing)==expected:
            shutil.copyfile(existing,dest);records[key]={'method':'verified_existing_copy'}
        else:
            choices=[u for u,t in links if ('cemaden' in t if key=='cemaden' else ('inpe' in t or 'inmet' in t or 'reuniao_ana_gaops' in t))]+[BASE+x for x in fallback[key]]
            for view in list(dict.fromkeys(choices))[:7]:
                try:
                    if not view.endswith('/view'):view=view.rstrip('/')+'/view'
                    r=session.get(view,timeout=(8,18));r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
                    downloads=[urljoin(view,a['href']) for a in s.find_all('a',href=True) if '@@download' in a['href']]
                    downloads.append(view[:-5]+'/@@download/file')
                    for url in list(dict.fromkeys(downloads))[:2]:
                        rr=session.get(url,timeout=(8,30));rr.raise_for_status();data=rr.content
                        if hashlib.sha256(data).hexdigest()!=expected:continue
                        dest.write_bytes(data);records[key]={'view':view,'download':url,'method':'official_copy_sha256_equal_to_attachment'};break
                    if dest.exists():break
                except Exception as e:print('Source attempt:',key,view,type(e).__name__,flush=True)
        assert dest.exists() and sha(dest)==expected,'Exact received source unavailable: '+key
        with fitz.open(dest) as d:assert len(d)==PAGES[key]
        records[key].update({'sha256':expected,'pages':PAGES[key],'matches_received_file':True})
        print('VERIFIED SOURCE',key,records[key],flush=True)
    return records

def data(out):
    rows=[]
    def add(k,local,var,value,unit,period,nature,page,note=''):
        rows.append([LABELS[k],local,var,str(value).replace('.',','),unit,period,nature,page,SITE+f'fontes/{k}.pdf#page={page}',note])
    for var,v,unit,period,nature,note in [('Chuva parcial novembro',55.0,'mm','01–09/11/2026','observado_parcial','Não é fechamento mensal'),('Chuva ano hidrológico',252.1,'mm','01/10–09/11/2026','observado_acumulado','Inclui novembro parcial'),('Chuva diária',3.7,'mm','09/11/2026','observado_diario','Incluída nos acumulados'),('Climatologia novembro',171.3,'mm','2001–2024','climatologia','Rótulo MClim_NOV'),('Climatologia OCT_NOV',264.7,'mm','2001–2024','climatologia','Confirmar composição temporal'),('Novembro relativo à MLT — anotação',11,'% MLT','Novembro/2026 parcial','anotacao_pendente_confirmacao','Não compatibilizado com os demais rótulos; não corrigido')]:add('cemaden','Bacia Paraíba do Sul',var,v,unit,period,nature,4,note)
    add('cemaden','Bacia Paraíba do Sul','Chuva GEFS em 14 dias',112,'mm','Rodada 10/11/2026 00 UTC','previsao_aproximada',9,'Valor central rotulado; dispersão dos membros')
    for var,lo,hi,unit in [('Climatologia NDJ precipitação',600,800,'mm'),('Climatologia NDJ temperatura',18,26,'°C')]:
        for bound,v in [('inferior',lo),('superior',hi)]:add('inpe','Recorte destacado Paraíba do Sul',var+' — limite '+bound,v,unit,'NDJ / referência 1981–2010','climatologia',11,'Faixa espacial; não previsão')
    for bound,v in [('inferior',1.27),('superior',1.77)]:add('cemaden','Recortes da previsão TSI','TSI-6 previsto — extremo '+bound,v,'adimensional','Próximos 30 dias / apresentação 10/11/2026','previsao',12,'Sem associação individual dos extremos a reservatórios')
    add('cemaden','Niño 3.4','Anomalia da temperatura da superfície do mar',2.3,'°C','Boletim 02/11/2026 reproduzido','observado_na_fonte',14,'Não é atualização independente')
    values=[('Jaguari',.79,1.44,1.75,1.91),('Funil',.23,1.15,1.42,2.07),('Santa Branca',-.33,.57,.62,1.78),('Paraibuna',-.29,.65,.70,1.89),('Santa Cecília',.10,1.08,1.27,2.03),('Ilha dos Pombos',-.18,.69,.80,1.79)]
    for local,s6,o6,s3,o3 in values:
        for var,vs,vo,pg in [('TSI-6',s6,o6,5),('TSI-3',s3,o3,6)]:
            for period,v in [('Setembro/2026',vs),('Outubro/2026',vo)]:add('cemaden',local,var,v,'adimensional',period,'indice_observado',pg,'Valor e classe conforme lâmina; não é armazenamento')
    assert len(rows)==38
    with (out/'indicadores.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['instituicao','sistema','variavel','valor','unidade','periodo','natureza','pagina_fonte','fonte_pdf','observacao']);w.writerows(rows)
    return rows

def pdf_build(soup,out,figures):
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    pdfmetrics.registerFont(TTFont('NT',font));pdfmetrics.registerFont(TTFont('NTB',bold));pdfmetrics.registerFontFamily('NT',normal='NT',bold='NTB',italic='NT',boldItalic='NTB')
    blue=colors.HexColor('#07536b')
    st={'body':ParagraphStyle('body',fontName='NT',fontSize=9.6,leading=14,spaceAfter=8), 'h2':ParagraphStyle('h2',fontName='NTB',fontSize=17,leading=22,textColor=blue,spaceAfter=14,keepWithNext=True), 'h3':ParagraphStyle('h3',fontName='NTB',fontSize=11,leading=15,textColor=colors.HexColor('#126f62'),spaceBefore=10,spaceAfter=7,keepWithNext=True), 'cell':ParagraphStyle('cell',fontName='NT',fontSize=8,leading=11), 'th':ParagraphStyle('th',fontName='NTB',fontSize=8,leading=11,textColor=colors.white), 'title':ParagraphStyle('title',fontName='NTB',fontSize=29,leading=36,textColor=blue,spaceAfter=22), 'toc':ParagraphStyle('toc',fontName='NT',fontSize=10,leading=15,spaceBefore=9)}
    def p(text,style='body'):return Paragraph(text,st[style])
    def markup(el):
        z=BeautifulSoup(str(el),'html.parser')
        for a in z.find_all('a'):a.unwrap()
        for b in z.find_all('strong'):b.name='b';b.attrs={}
        for e in z.find_all('em'):e.name='i';e.attrs={}
        root=z.find();return root.decode_contents()
    def furniture(c,doc):
        w,h=c._pagesize;c.saveState();c.setFillColor(blue);c.setFont('NT',7)
        c.drawString(48,h-27,'SOE/ANA — GABINETE | 116ª GAOPS | 10/11/2026 | Prévia documental 0.2')
        c.setStrokeColor(colors.HexColor('#c5d8df'));c.line(48,h-34,w-48,h-34);c.line(48,47,w-48,47)
        c.drawCentredString(w/2,34,'Supervisionado por '+NAME+' — Especialista em Geoprocessamento')
        c.drawCentredString(w/2,23,'Gabinete/SOE/ANA · Elaboração com suporte de IA · Discussão interna');c.restoreState()
    class Doc(BaseDocTemplate):
        def __init__(self,path):
            super().__init__(str(path),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=52,bottomMargin=60,title='116ª GAOPS — Nota Técnica — Paraíba do Sul',author=NAME)
            self.addPageTemplates([PageTemplate(id='portrait',frames=[Frame(48,60,A4[0]-96,A4[1]-112,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],pagesize=A4,onPage=furniture),PageTemplate(id='wide',frames=[Frame(48,60,landscape(A4)[0]-96,landscape(A4)[1]-112,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],pagesize=landscape(A4),onPage=furniture)])
            self.headings=[]
        def beforeDocument(self):self.headings=[]
        def afterFlowable(self,f):
            if hasattr(f,'bookmark'):
                self.canv.bookmarkPage(f.bookmark);self.notify('TOCEntry',(0,f.getPlainText(),self.page,f.bookmark));self.headings.append([1,f.getPlainText(),self.page])
    def section_story(sec,wide=False):
        result=[];width=(landscape(A4)[0] if wide else A4[0])-96
        for el in sec.children:
            if not getattr(el,'name',None):continue
            if el.name in ['h2','h3']:
                para=p(html.escape(el.get_text(' ',strip=True)),el.name)
                if el.name=='h2':para.bookmark=sec['id']
                result.append(para)
            elif el.name=='p':result.append(p(markup(el)))
            elif 'tablewrap' in el.get('class',[]):
                table=el.find('table');trs=table.find_all('tr');n=len(trs[0].find_all(['th','td']))
                ratios=([.21,.34,.45] if n==3 else [.28,.12,.12,.22,.26] if n==5 else [1/n]*n)
                cells=[]
                for tr in trs:
                    cells.append([p(html.escape(td.get_text(' ',strip=True)),'th' if td.name=='th' else 'cell') for td in tr.find_all(['th','td'])])
                t=Table(cells,colWidths=[width*r for r in ratios],repeatRows=1,hAlign='LEFT')
                t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),blue),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#c5d8df')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f7f8')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));result.extend([t,Spacer(1,12)])
        return result
    sections=soup.select('main > section')
    story=[Spacer(1,50),p('116ª Reunião do GAOPS','title'),p('Nota Técnica — PARAÍBA DO SUL','h2'),p('10 de novembro de 2026 · reunião programada para 15h00'),Spacer(1,16),p('<b>PRÉVIA DOCUMENTAL 0.2</b>'),p('INPE/INMET e CEMADEN analisados. ONS ainda não recebido; debate e encerramento não informados.'),p('Texto integral, cruzamentos técnicos, Anexo I e 24 reproduções identificadas. Observações, climatologias, previsões e recomendações são distintas.'),Spacer(1,30),p('<b>Supervisionado por '+NAME+'</b>'),p('Especialista em Geoprocessamento<br/>Gabinete da Superintendência de Operações e Eventos Críticos — SOE/ANA'),p('Elaboração com suporte de inteligência artificial (IA).'),Spacer(1,20),p('Protótipo técnico em repositório pessoal. Não substitui ata, ato administrativo ou publicação institucional da ANA.'),PageBreak(),p('Sumário','h2')]
    toc=TableOfContents();toc.levelStyles=[st['toc']];story.append(toc)
    for sec in sections:
        if sec['id']=='anexo-i':story.extend([NextPageTemplate('wide'),PageBreak()]);story.extend(section_story(sec,True))
        else:story.append(PageBreak());story.extend(section_story(sec))
    raw=out/'documentos/_texto.pdf';doc=Doc(raw);doc.multiBuild(story);tocrows=list(doc.headings)
    full=fitz.open(raw);annex_start=next(r[2]-1 for r in tocrows if r[1].startswith('ANEXO I'));annex_end=len(full)
    ann=fitz.open();ann.insert_pdf(full,from_page=annex_start,to_page=annex_end-1)
    def write(page,rect,text,size=9,bold=False):
        fontname='NTB' if bold else 'NT';fp=globals().get('unused',None)
        page.insert_font(fontname=fontname,fontfile=('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else font))
        ret=page.insert_textbox(rect,text,fontname=fontname,fontsize=size,color=(.03,.32,.42));assert ret>=0,('Overflow',text)
    lastkey=None
    for fig in figures:
        w,h=landscape(A4);page=full.new_page(width=w,height=h)
        if fig['key']!=lastkey:tocrows.append([1,'ANEXO GRÁFICO — '+LABELS[fig['key']],len(full)]);lastkey=fig['key']
        write(page,fitz.Rect(45,25,w-45,60),f'Figura {fig["number"]} — {fig["title"]}',12,True)
        source=fitz.open(out/'fontes'/(fig['key']+'.pdf'));page.show_pdf_page(fitz.Rect(45,66,w-45,h-108),source,fig['page']-1);source.close()
        write(page,fitz.Rect(45,h-101,w-45,h-56),fig['caption']+' Fonte: '+LABELS[fig['key']]+', p. '+str(fig['page'])+'. Reprodução da apresentação recebida.',8.3)
        write(page,fitz.Rect(45,h-47,w-45,h-19),'Supervisão '+NAME+' · Especialista em Geoprocessamento — Gabinete/SOE/ANA · suporte de IA',7)
    def folios(document):
        for i,page in enumerate(document):write(page,fitz.Rect(page.rect.width-145,page.rect.height-16,page.rect.width-24,page.rect.height-2),f'Página {i+1} de {len(document)}',7)
    folios(ann);ann.set_metadata({'title':'Anexo I — 116ª GAOPS — Reunião em números','author':NAME});ann.save(out/'documentos'/ANNEX,garbage=3,deflate=True);ann.close()
    folios(full);full.set_toc(tocrows);full.set_metadata({'title':'NT 116ª GAOPS — 10/11/2026 — Prévia documental 0.2','author':NAME,'subject':'INPE/INMET e CEMADEN; ONS pendente. Anexo I e 24 reproduções.'});full.save(out/'documentos'/PDF,garbage=3,deflate=True);full.close();raw.unlink()
    with fitz.open(out/'documentos'/PDF) as check:
        alltext=norm(' '.join(page.get_text() for page in check));missing=[]
        for sec in sections:
            for el in sec.select('p,th,td'):
                if el.find_parent(class_='gallery') or el.get('class')==['download-access']:continue
                text=norm(el.get_text(' ',strip=True))
                if text and text not in alltext:missing.append(el.get_text(' ',strip=True)[:140])
        assert not missing,('Missing published text in PDF',missing[:8])
        count=len(check)
        for i in [0,1,2,annex_start,annex_end-1,annex_end,count-1]:check[i].get_pixmap(matrix=fitz.Matrix(1.1,1.1),alpha=False).save(out/'qa'/f'page-{i+1:02}.png')
    return {'pdf_pages':count,'annex_pages':annex_end-annex_start,'annex_start_page':annex_start+1,'toc':tocrows,'text_and_tables_preserved':True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--sources',type=Path);args=ap.parse_args();out=args.out
    for sub in ['fontes','assets','documentos','qa']:(out/sub).mkdir(parents=True,exist_ok=True)
    sources=obtain(out,args.sources)
    soup=BeautifulSoup((ROOT/'index.html').read_text(encoding='utf-8'),'html.parser')
    for tag in soup.select('.gallery,.download-access'):tag.decompose()
    assert [x['id'] for x in soup.select('main > section')][-2:]==['fontes','anexo-i']
    figures=[]
    for key,specs in FIGS.items():
        gallery=soup.new_tag('div',attrs={'class':'gallery'});source=fitz.open(out/'fontes'/(key+'.pdf'))
        for pg,title,caption in specs:
            page=source[pg-1];pix=page.get_pixmap(matrix=fitz.Matrix(1800/page.rect.width,1800/page.rect.width),alpha=False)
            relative=f'assets/{key}_{pg:02}.jpg';pix.save(out/relative,jpg_quality=93)
            fig={'number':len(figures)+1,'key':key,'page':pg,'title':title,'caption':caption,'src':relative,'width':pix.width,'height':pix.height};figures.append(fig)
            f=soup.new_tag('figure');a=soup.new_tag('a',href=relative,attrs={'target':'_blank','rel':'noopener'});im=soup.new_tag('img',src=relative,alt=title,width=str(pix.width),height=str(pix.height),loading='lazy');a.append(im);f.append(a)
            fc=soup.new_tag('figcaption');b=soup.new_tag('strong');b.string=f'Figura {fig["number"]} — {title}';fc.append(b);fc.append(caption)
            sp=soup.new_tag('span',attrs={'class':'source'});sp.string=f'Fonte: {LABELS[key]}, página {pg}. Reprodução do PDF recebido.';fc.append(sp)
            link=soup.new_tag('a',href=f'fontes/{key}.pdf#page={pg}');link.string='Consultar apresentação original';fc.append(link);f.append(fc);gallery.append(f)
        source.close();soup.find(id=key).append(gallery)
    rows=data(out)
    status=soup.find(id='publication-status');status.clear();status.append('PRÉVIA DOCUMENTAL 0.2 — INPE/INMET e CEMADEN, cruzamentos, Anexo I, 24 reproduções e 38 registros numéricos. ONS ainda não recebido; deliberações e encerramento não informados. NT integral e apresentações hospedadas.')
    for id_,href,label in [('pdf-action','documentos/'+PDF,'Baixar NT completa · PDF'),('csv-action','indicadores.csv','Dados e indicadores · CSV')]:
        old=soup.find(id=id_);a=soup.new_tag('a',href=href,id=id_,attrs={'download':'','class':'primary' if id_=='pdf-action' else ''});a.string=label;old.replace_with(a)
    for key in HASHES:
        p=soup.new_tag('p',attrs={'class':'download-access'});a=soup.new_tag('a',href=f'fontes/{key}.pdf');a.string='Apresentação integral — '+LABELS[key]+' · PDF';p.append(a);soup.find(id='fontes').append(p)
    p=soup.new_tag('p',attrs={'class':'download-access'});a=soup.new_tag('a',href='documentos/'+ANNEX,attrs={'download':''});a.string='Consultar somente o Anexo I · PDF';p.append(a);soup.find(id='anexo-i').append(p)
    # Main PDF uses the same analytical DOM, without galleries; source slides follow as native PDF pages.
    analytical=BeautifulSoup(str(soup),'html.parser')
    for el in analytical.select('.gallery,.download-access'):el.decompose()
    info=pdf_build(analytical,out,figures)
    (out/'index.html').write_text(str(soup),encoding='utf-8')
    manifest={'meeting':'116ª Reunião do GAOPS','date':'2026-11-10','version':'0.2','status':'Prévia documental; ONS pendente; encerramento não informado','generated_at':datetime.now(timezone.utc).isoformat(),'sources':sources,'figure_count':len(figures),'indicator_rows':len(rows),'figures':figures,**info,'pdf_sha256':sha(out/'documentos'/PDF),'annex_sha256':sha(out/'documentos'/ANNEX),'csv_sha256':sha(out/'indicadores.csv')}
    (out/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('COMPLETE',json.dumps({k:v for k,v in manifest.items() if k not in ['figures','sources','toc']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
