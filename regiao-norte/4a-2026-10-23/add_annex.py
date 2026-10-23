#!/usr/bin/env python3
"""Editorial revision 1.1: reader-facing numerical annex; CSV stays byte-identical.
This script changes only this meeting and verifies preservation of technical pages.
"""
from pathlib import Path
import argparse,csv,hashlib,html,json,re,shutil
import fitz
from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,PageBreak

PDF='NT_Regiao_Norte_4a_23-10-2026.pdf'
ANNEX='Anexo_I_Regiao_Norte_23-10-2026.pdf'
TITLE='ANEXO I — Resumo para o Relatório Anual / reunião em números'
NAME='José Aguiar de Lima Jr.'
ROLE='Especialista em Geoprocessamento'
BLUE='#215575';TEAL='#146E60';GREY='#526C78'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def esc(s):return html.escape(str(s),quote=True)
def number(v,signed=False):
    if ',' in v:return v
    n=int(v);out=f'{abs(n):,}'.replace(',','.')
    return ('−' if n<0 else '+' if signed and n>0 else '')+out

def data_blocks(rows):
    assert len(rows)==53,'Unexpected analytical base; review rather than overwrite'
    used=set()
    def get(inst,local,indicator):
        matches=[(i,r) for i,r in enumerate(rows) if r['instituicao']==inst and r['local']==local and r['indicador']==indicator]
        assert len(matches)==1,(inst,local,indicator)
        i,r=matches[0];used.add(i);return r
    specs=[('Branco','Boa Vista / Branco','Boa Vista','Seca severa'),('Negro','Manaus / Negro','Manaus','Seca severa'),('Tapajós','Santarém / Tapajós','Santarém','Seca fraca'),('Amazonas','Óbidos / Amazonas','Óbidos','Normal'),('Madeira','Santo Antônio / Madeira','UHE Santo Antônio','Normal'),('Xingu','Belo Monte / Xingu','UHE Belo Monte','Seca moderada'),('Tocantins','Tucuruí','UHE Tucuruí','Seca severa'),('Araguaia','Araguatins','Araguatins','Seca severa'),('Tocantins','Descarreto','Descarreto','Seca severa'),('Araguaia','Conceição do Araguaia','Conceição do Araguaia','Seca severa'),('Solimões','Manacapuru','Manacapuru','Normal'),('Solimões','Tabatinga','Tabatinga','Normal'),('Purus, conforme CEMADEN','Beruri / Purus na fonte','Beruri*','Normal'),('Juruá','Santos Dumont / Juruá','Santos Dumont','Normal')]
    tsi=[]
    for river,key,station,cls in specs:
        r=get('CEMADEN',key,'TSI-12');tsi.append([river,station,r['valor'],cls,'C, p. '+r['pagina_fonte']])
    cota=get('CEMADEN','Boa Vista','Cota diária')['valor']
    specs=[('Solimões','Tabatinga','Negativa leve'),('Acre','Rio Branco/AC','Normalidade'),('Solimões, conforme CENSIPAM','Beruri','Negativa leve'),('Negro','Cucuí','Normalidade'),('Branco','Boa Vista','Negativa severa'),('Negro*','Manaus','Negativa leve'),('Mamoré','Guajará-Mirim','Normalidade'),('Madeira','Porto Velho','Normalidade'),('Amazonas','Óbidos','Negativa leve'),('Tapajós','Itaituba','Negativa leve'),('Tapajós','Santarém','Negativa leve'),('Iriri / Xingu','Pedra do Ó','Negativa moderada'),('Araguaia','Xambioá','Negativa moderada'),('Tocantins','Marabá','Negativa leve')]
    delta=[]
    for river,station,cls in specs:
        r=get('CENSIPAM',station,'Variação de cota em 15 dias');delta.append([river,station,number(r['valor'],True),cls,'P, p. '+r['pagina_fonte']])
    hydro=[]
    for river,plant in [('Madeira','Santo Antônio'),('Xingu','Pimental'),('Araguari','Ferreira Gomes'),('Teles Pires / Tapajós','São Manoel'),('Uatumã','Balbina')]:
        a=get('ONS',plant,'Vazão natural média');b=get('ONS',plant,'Vazão natural relativa à MLT');c=get('ONS',plant,'Vazão natural média — cenário inferior');d=get('ONS',plant,'Cenário inferior relativo à MLT')
        hydro.append([river+' / '+plant,number(a['valor']),b['valor']+'%',number(c['valor']),d['valor']+'%','O, p. '+a['pagina_fonte']])
    ops=[]
    for local,var in [('Subsistema Norte','Energia armazenada'),('Balbina','Volume útil'),('Balbina','Vazão afluente'),('Balbina','Vazão defluente')]:
        r=get('ONS',local,var);ops.append([local,var,r['valor']+' '+r['unidade'],r['periodo'],'O, p. '+r['pagina_fonte']])
    assert used==set(range(53)),'Not all approved records are represented'
    return [
      dict(title='I.1 — Índices de seca e cota de referência',intro='CEMADEN • TSI-12 de outubro de 2026, parcial • Índice adimensional de precipitação e cota/vazão na janela de 12 meses. As classes são as informadas na apresentação.',tables=[dict(headers=['Bacia / sistema','Estação / recorte','TSI-12','Classe na fonte','Fonte'],rows=tsi,widths=[175,200,70,190,95])],notes=[f'<b>Cota diária — Boa Vista / rio Branco:</b> {cota} cm em 22/10/2026, referidos ao zero da régua local [C, p. 12]. Não é profundidade do rio nem volume disponível.','<b>Leitura:</b> índices normais em um recorte não implicam cota normal em cada dia. *Beruri é associado ao Purus no CEMADEN e ao Solimões no CENSIPAM; não fundir séries sem confirmar o código da estação.','<b>Uso anual:</b> manter a janela de 12 meses e o status parcial. TSI não é vazão, percentual de armazenamento ou contagem de municípios afetados.']),
      dict(title='I.2 — Variação dos níveis nos sistemas monitorados',intro='CENSIPAM / SipamHidro • Saldo de variação da cota em 15 dias nas lâminas apresentadas em 23/10/2026. Valores positivos indicam elevação; negativos, redução. A classe é a anomalia hidrológica da fonte.',tables=[dict(headers=['Rio / sistema','Estação','Variação (cm)','Anomalia na fonte','Fonte'],rows=delta,widths=[225,165,95,150,95])],notes=['<b>Leitura:</b> a reação nos últimos dias em Tabatinga e Boa Vista pode coexistir com saldo negativo no intervalo de 15 dias. A variação não representa cota absoluta nem vazão.','<b>Rastreabilidade:</b> *a lâmina 8 do CENSIPAM escreve “Solimões” para Manaus, enquanto a lâmina 30 identifica rio Negro. A divergência está registrada na NT. As janelas devem ser conferidas antes de comparar reuniões.','<b>Uso anual:</b> intervalos de 15 dias podem se sobrepor entre reuniões. Não somar esses saldos como se fossem uma série contínua anual.']),
      dict(title='I.3 — Vazões naturais, armazenamento e operação',intro='ONS • Setembro/2026 é observação mensal; outubro/2026 é o cenário inferior apresentado, condicionado ao SMAP/ONS e à chuva ECMWF. As duas naturezas estão separadas nas colunas.',tables=[dict(headers=['Bacia / aproveitamento','Setembro observado\nQ natural (m³/s)','Setembro\n% MLT','Outubro: cenário inferior\nQ natural (m³/s)','Outubro\n% MLT','Fonte'],rows=hydro,widths=[210,125,75,150,75,95]),dict(title='Posições de estoque e operação — até 22/10/2026',headers=['Recorte','Variável','Valor','Data / referência','Fonte'],rows=ops,widths=[145,165,130,195,95])],notes=['<b>Distinções:</b> MLT = média de longo termo; EAR = energia armazenada; VU = volume útil. 65% de EAR do Subsistema Norte não equivale ao VU de cada usina. Em Balbina, as vazões do painel não são médias mensais naturais.','<b>Registro para a memória anual:</b> a próxima reunião, em 04/12/2026, será denominada Sala de Crise em razão do El Niño, conforme informado pelo responsável no encerramento. Não equivale a nova autorização operativa.','<b>Subsídio ao Conjuntura:</b> este anexo é uma síntese da reunião, não uma estatística anual homologada. Consolidar observados comparáveis, substituir parciais apenas com rastreabilidade e manter previsões fora das séries observadas.'])]

def styles():
    pdfmetrics.registerFont(TTFont('NT',FONT));pdfmetrics.registerFont(TTFont('NTB',BOLD));pdfmetrics.registerFontFamily('NT',normal='NT',bold='NTB',italic='NT',boldItalic='NTB')
    return dict(title=ParagraphStyle('title',fontName='NTB',fontSize=14,leading=18,textColor=colors.HexColor(BLUE),spaceAfter=6),sub=ParagraphStyle('sub',fontName='NTB',fontSize=11,leading=14,textColor=colors.HexColor(TEAL),spaceAfter=5),intro=ParagraphStyle('intro',fontName='NT',fontSize=9,leading=12,spaceAfter=8),cell=ParagraphStyle('cell',fontName='NT',fontSize=9,leading=11.5),head=ParagraphStyle('head',fontName='NTB',fontSize=8.7,leading=11,textColor=colors.white),note=ParagraphStyle('note',fontName='NT',fontSize=8.3,leading=11,spaceAfter=4))

def furniture(c,doc):
    w,h=doc.pagesize;c.saveState();c.setStrokeColor(colors.HexColor('#BDD1DC'));c.setFillColor(colors.HexColor(GREY));c.setFont('NT',7.2)
    c.drawString(48,h-25,'SOE/ANA — GABINETE | Região Norte — 4ª reunião — 23/10/2026 | Revisão 1.1');c.line(48,h-32,w-48,h-32);c.line(48,47,w-48,47)
    c.drawCentredString(w/2,35,f'Supervisionado por {NAME} · {ROLE}');c.drawCentredString(w/2,25,'Gabinete/SOE/ANA · Elaboração com suporte de inteligência artificial (IA)');c.drawRightString(w-48,14,f'Anexo I • {doc.page} / 3');c.restoreState()

def make_annex(out,blocks):
    st=styles();story=[]
    for i,block in enumerate(blocks):
        if i:story.append(PageBreak())
        story.extend([Paragraph(TITLE,st['title']),Paragraph(block['title'],st['sub']),Paragraph(esc(block['intro']),st['intro'])])
        for spec in block['tables']:
            if spec.get('title'):story.extend([Spacer(1,8),Paragraph(spec['title'],st['sub'])])
            content=[[Paragraph(esc(v).replace('\n','<br/>'),st['head']) for v in spec['headers']]]
            content.extend([[Paragraph(esc(v),st['cell']) for v in row] for row in spec['rows']])
            t=Table(content,colWidths=spec['widths'],repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(BLUE)),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#C7D7DF')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F2F6F7')]),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]));story.append(t)
        story.append(Spacer(1,8));story.extend(Paragraph(note,st['note']) for note in block['notes'])
        story.append(Paragraph('Fontes: C = CEMADEN/MCTI; P = CENSIPAM/SipamHidro; O = ONS. Páginas físicas das apresentações. Base tabular de 53 registros preservada.',st['note']))
    path=out/'documentos'/ANNEX;path.parent.mkdir(exist_ok=True)
    SimpleDocTemplate(str(path),pagesize=landscape(A4),leftMargin=48,rightMargin=48,topMargin=43,bottomMargin=56,title=TITLE,author=NAME).build(story,onFirstPage=furniture,onLaterPages=furniture)
    with fitz.open(path) as doc:
        assert len(doc)==3,f'Annex overflowed to {len(doc)} pages'
        for i,p in enumerate(doc):assert f'I.{i+1}' in p.get_text()
    return path

def write_text(page,rect,text,size=9,bold=False,align=0):
    name='NTA_B' if bold else 'NTA';font=BOLD if bold else FONT;page.insert_font(fontname=name,fontfile=font)
    result=page.insert_textbox(rect,text,fontname=name,fontfile=font,fontsize=size,color=(.13,.33,.46),align=align);assert result>=0,(text,result)

def clear(page,rect):
    page.add_redact_annot(rect,fill=(1,1,1));page.apply_redactions(images=0,graphics=0)

def merge_pdf(base,out,annex):
    src=base/'documentos'/PDF;old_hash=sha(src);doc=fitz.open(src);assert len(doc)==60,'Unexpected revision; reconcile first'
    toc=doc.get_toc();old_text=[p.get_text(clip=fitz.Rect(40,45,p.rect.width-40,p.rect.height-59)) for p in doc]
    assert toc[13][1].startswith('ANEXO A') and toc[13][2]==23
    at=22;ann=fitz.open(annex);doc.insert_pdf(ann,start_at=at);ann.close();total=len(doc);assert total==63
    for old_i in range(60):
        new_i=old_i if old_i<at else old_i+3;p=doc[new_i];areas=p.search_for(f'Página {old_i+1} de 60');assert len(areas)==1
        clear(p,areas[0]+(-1,-1,2,1));write_text(p,fitz.Rect(p.rect.width-135,p.rect.height-25,p.rect.width-48,p.rect.height-10),f'Página {new_i+1} de {total}',7.3,align=2)
    for i in range(3):
        p=doc[at+i];areas=p.search_for(f'Anexo I • {i+1} / 3');assert len(areas)==1
        clear(p,areas[0]+(-1,-1,2,1));write_text(p,fitz.Rect(p.rect.width-160,p.rect.height-25,p.rect.width-48,p.rect.height-10),f'Página {at+i+1} de {total}',7.3,align=2)
    p=doc[0];area=p.search_for('1.0 — 23/10/2026. Não substitui ata ou ato administrativo.');assert len(area)==1
    clear(p,area[0]+(-1,-1,2,1));write_text(p,fitz.Rect(area[0].x0,area[0].y0-1,535,area[0].y0+19),'1.1 — 23/10/2026. Inclusão do Anexo I; conteúdo técnico preservado.',7.3)
    write_text(p,fitz.Rect(57,580,538,620),'Revisão 1.1: Anexo I — síntese numérica nas páginas 23–25.\nOs 53 registros da base tabular e as 38 figuras permanecem inalterados.',8.5)
    p=doc[21];write_text(p,fitz.Rect(57,747,538,777),'Anexo I — Reunião em números: páginas 23–25 desta revisão.\nAnexos gráficos A–E preservados, com paginação atualizada.',7.5)
    new_toc=[list(x) for x in toc[:13]]+[[1,TITLE,23]]+[[level,title,page+3] for level,title,page in toc[13:]]
    p=doc[1]
    for link in p.get_links():p.delete_link(link)
    clear(p,fitz.Rect(53,48,543,749));write_text(p,fitz.Rect(57,52,538,80),'SUMÁRIO',15,bold=True);y=99
    for level,title,page_number in new_toc:
        display='ANEXO I — Resumo anual / reunião em números' if title==TITLE else title
        write_text(p,fitz.Rect(57,y,513,y+23),display,8.8,bold=title==TITLE);write_text(p,fitz.Rect(514,y,538,y+23),str(page_number),8.8,align=2)
        p.insert_link({'kind':fitz.LINK_GOTO,'from':fitz.Rect(56,y,539,y+23),'page':page_number-1});y+=29
    doc.set_toc(new_toc);meta=doc.metadata;meta.update({'title':'Região Norte — 4ª reunião — NT integral — revisão 1.1','subject':'Inclusão do Anexo I — síntese numérica para Relatório Anual e subsídio ao Conjuntura','author':f'Supervisão: {NAME} — {ROLE} — SOE/ANA; suporte de IA'});doc.set_metadata(meta)
    dest=out/'documentos'/PDF;doc.save(dest,garbage=3,deflate=True);doc.close();updated=fitz.open(dest);original=fitz.open(src)
    for old_i in range(60):
        new_i=old_i if old_i<at else old_i+3;p=updated[new_i]
        if old_i not in (0,1,21):assert p.get_text(clip=fitz.Rect(40,45,p.rect.width-40,p.rect.height-59))==old_text[old_i],f'Technical page changed: {old_i+1}'
        assert [(im['bbox'],im['digest']) for im in original[old_i].get_image_info(hashes=True)]==[(im['bbox'],im['digest']) for im in p.get_image_info(hashes=True)],f'Image changed: {old_i+1}'
    assert len(updated)==63 and len(updated.get_toc())==19
    assert sum(len(p.get_image_info()) for p in updated)==38
    for i,p in enumerate(updated):assert f'Página {i+1} de 63' in p.get_text()
    original.close();updated.close();return old_hash

def render_html(blocks):
    parts=[f'<section class="chapter" id="anexo-i"><h2>{esc(TITLE)}</h2><p>Quadro de consulta rápida por bacia e sistema. Os mesmos 53 registros da base tabular são apresentados em tabelas de leitura, sem necessidade de ferramenta analítica. Revisão editorial 1.1.</p>']
    for block in blocks:
        parts.extend([f'<h3>{esc(block["title"])}</h3>',f'<p>{esc(block["intro"])}</p>'])
        for spec in block['tables']:
            if spec.get('title'):parts.append('<h4>'+esc(spec['title'])+'</h4>')
            heads=''.join('<th>'+esc(v).replace('\n','<br>')+'</th>' for v in spec['headers'])
            body=''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in spec['rows'])
            parts.append('<div class="tablewrap"><table><thead><tr>'+heads+'</tr></thead><tbody>'+body+'</tbody></table></div>')
        parts.extend('<p class="small">'+x+'</p>' for x in block['notes'])
    parts.append('<p class="small">Fontes: C = CEMADEN/MCTI; P = CENSIPAM/SipamHidro; O = ONS. Páginas físicas das apresentações. As classes foram preservadas; os anexos gráficos continuam disponíveis.</p>')
    parts.append(f'<p><a href="documentos/{ANNEX}" download>Consultar Anexo I — PDF (3 páginas)</a> · <a href="indicadores.csv" download>Base tabular completa — CSV</a></p></section>');return ''.join(parts)

def edit_html(base,out,blocks):
    s=BeautifulSoup((base/'index.html').read_text(encoding='utf-8'),'html.parser');assert s.find(id='anexo-i') is None,'Annex already present'
    sections={sec['id']:str(sec) for sec in s.select('main section.chapter') if sec.get('id')};figures=[str(f) for f in s.select('figure')];credits=[str(c) for c in s.select('.credit')]
    annex=BeautifulSoup(render_html(blocks),'html.parser').section;s.find(id='fontes').insert_after(annex)
    data=s.select_one('header .actions a[href="indicadores.csv"]');assert data is not None
    a=s.new_tag('a',href='#anexo-i',attrs={'title':'Consultar o quadro-síntese numérico e acessar seu PDF de 3 páginas'});a.string='Anexo I — Reunião em números';data.insert_after(a)
    group=s.new_tag('div',attrs={'class':'nt-data-actions','role':'group','aria-label':'Síntese numérica e dados analíticos'});data.insert_before(group);group.append(data.extract());group.append(a.extract())
    style=s.new_tag('style',attrs={'id':'annex-actions-style'});style.string='.actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.nt-data-actions{grid-column:1/-1;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.actions a{min-width:0;min-height:50px}.nt-data-actions a{width:100%}@media(max-width:800px){.actions,.nt-data-actions{grid-template-columns:1fr}}@media print{header .actions{display:none}}';s.head.append(style)
    li=s.new_tag('li');a=s.new_tag('a',href='#anexo-i');a.string='Anexo I — Resumo anual / reunião em números';li.append(a);s.select_one('.contents ul').append(li)
    a=s.new_tag('a',href='#anexo-i');a.string='Reunião em números';s.nav.append(a)
    for text in list(s.header.find_all(string=True)):
        if 'Edição 1.0' in text:text.replace_with(text.replace('Edição 1.0','Edição 1.1 — Anexo I incluído'))
    p=s.new_tag('p',attrs={'class':'small'});p.string='Revisão 1.1: inclusão do Anexo I numérico; texto analítico, figuras e CSV preservados. O PDF integral contém 63 páginas; Anexo I nas páginas 23–25.';s.footer.append(p)
    for key,value in sections.items():assert str(s.find(id=key))==value,'Original chapter modified: '+key
    assert [str(f) for f in s.select('figure')]==figures and [str(c) for c in s.select('.credit')]==credits
    (out/'index.html').write_text(str(s),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();base=args.base.resolve();out=args.output.resolve();assert base!=out;out.mkdir(parents=True,exist_ok=True);(out/'documentos').mkdir(exist_ok=True)
    manifest=json.loads((base/'manifesto.json').read_text(encoding='utf-8'));assert str(manifest.get('version','1.0'))=='1.0','Revision already changed; do not apply twice'
    assert sha(base/'documentos'/PDF)==manifest['pdf_sha256'],'PDF does not match current published manifest'
    csv_hash=sha(base/'indicadores.csv');rows=list(csv.DictReader((base/'indicadores.csv').open(encoding='utf-8-sig'),delimiter=';'))
    blocks=data_blocks(rows);annex=make_annex(out,blocks);previous_pdf=merge_pdf(base,out,annex);edit_html(base,out,blocks)
    assert sha(base/'indicadores.csv')==csv_hash;shutil.copyfile(base/'indicadores.csv',out/'indicadores.csv')
    manifest['version']='1.1';manifest['pdf_pages']=63;manifest['pdf_sha256']=sha(out/'documentos'/PDF);manifest['checks']['toc_entries']=19;manifest.setdefault('distribution_optimization',{})['pdf_bytes']=(out/'documentos'/PDF).stat().st_size
    manifest['anexo_i']={'title':TITLE,'web_anchor':'anexo-i','pdf':'documentos/'+ANNEX,'pdf_sha256':sha(annex),'pages':3,'records':53,'button_after':'Dados e indicadores'}
    manifest['editorial_revision']={'revision':'1.1','change':'Inclusão do Anexo I — Resumo anual / reunião em números','annex_pages':[23,24,25],'annex_standalone_pages':3,'previous_pdf_sha256':previous_pdf,'csv_sha256':csv_hash,'csv_unchanged':True,'records_represented':53,'original_figures_preserved':True,'original_analysis_preserved':True,'annual_note':'Retratos de reuniões não constituem automaticamente estatísticas anuais; evitar duplicações, sobreposições e mistura com previsões.'}
    (out/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');(out/'ANEXO_I.json').write_text(json.dumps(blocks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest['editorial_revision'],ensure_ascii=False,indent=2));print('COMPLETE: 63-page integral PDF; 3-page annex; 53 records; CSV, analysis and figures unchanged.',flush=True)

if __name__=='__main__':main()
