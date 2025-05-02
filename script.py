import csv
import re
from collections import Counter

# Raw data input as a multiline string
raw_data = """
Nome, Categoria, Email, Perfil
Alberto Cardoso, Professor Associado, alberto@dei.uc.pt, http://faculty.uc.pt/uc24774
Amílcar Cardoso, Professor Catedrático, amilcar@dei.uc.pt, http://faculty.uc.pt/uc24291
António Dias de Figueiredo, Professor Catedrático Aposentado, adf@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc41097/pt
António Dourado, Professor Catedrático Jubilado, dourado@dei.uc.pt, https://www.cisuc.uc.pt/en/people/antonio-dourado
António Mendes, Professor Associado c/ Agregação, toze@dei.uc.pt, http://faculty.uc.pt/uc22803
Bernardete Ribeiro, Professora Catedrática Jubilada, bribeiro@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc25930/en
Bruno Sousa, Professor Auxiliar, bmsousa@dei.uc.pt, http://apps.uc.pt/mypage/faculty/uc43546
Carlos Bento, Professor Associado c/ Agregação, bento@dei.uc.pt, https://www.cisuc.uc.pt/en/people/carlos-bento
Carlos Fonseca, Professor Associado, cmfonsec@dei.uc.pt, http://faculty.uc.pt/uc26853
Catarina Silva, Professora Associada, catarina@dei.uc.pt, http://apps.uc.pt/mypage/faculty/uc45296
César Teixeira, Professor Associado c/ Agregação, cteixei@dei.uc.pt, http://faculty.uc.pt/uc26769
Edmundo Monteiro, Professor Catedrático, edmundo@dei.uc.pt, https://apps.uc.pt/mypage/faculty/edmundo
Ernesto Costa, Professor Catedrático Jubilado, ernesto@dei.uc.pt, https://apps.uc.pt/mypage/faculty/ernestojfc/en
Evgheni Polisciuc, Professor Auxiliar, evgheni@dei.uc.pt, http://apps.uc.pt/mypage/faculty/uc41408
Fernando Barros, Professor Auxiliar, barros@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc24876/en
Fernando Boavida, Professor Catedrático, boavida@dei.uc.pt, http://faculty.uc.pt/uc24338
Filipe Araújo, Professor Associado c/ Agregação, filipius@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc26622
Henrique Madeira, Professor Catedrático, henrique@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc00007515/en
Hugo Gonçalo Oliveira, Professor Associado, hroliv@dei.uc.pt, http://faculty.uc.pt/uc41089
Jacinto Estima, Professor Auxiliar, estima@dei.uc.pt, https://jestima.github.io/
João Barata, Professor Auxiliar, barata@dei.uc.pt, http://apps.uc.pt/mypage/faculty/uc44366
João Campos, Professor Auxiliar, jrcampos@dei.uc.pt, https://www.cisuc.uc.pt/en/people/joao-campos
João Gabriel Silva, Professor Catedrático, jgabriel@dei.uc.pt, https://apps.uc.pt/mypage/faculty/jgsilva
João Nuno Correia, Professor Auxiliar, jncor@dei.uc.pt, http://apps.uc.pt/mypage/faculty/uc40050
Joel Arrais, Professor Associado, jpa@dei.uc.pt, http://apps.uc.pt/mypage/faculty/uc41532
Jorge Cardoso, Professor Auxiliar, jorgecardoso@dei.uc.pt, http://faculty.uc.pt/uc42867
Jorge Granjal, Professor Auxiliar, jgranjal@dei.uc.pt, http://faculty.uc.pt/uc25612
Jorge Henriques, Professor Associado c/ Agregação, jh@dei.uc.pt, http://faculty.uc.pt/uc22824
Karima Castro, Professora Auxiliar, kcastro@dei.uc.pt, https://www.cisuc.uc.pt/en/people/karima-velasquez
Licínio Roque, Professor Associado, lir@dei.uc.pt, http://apps.uc.pt/mypage/faculty/uc26082
Luís Macedo, Professor Auxiliar, macedo@dei.uc.pt, http://faculty.uc.pt/uc26618/en
Luís Paquete, Professor Associado, paquete@dei.uc.pt, http://faculty.uc.pt/uc26679
Marco Simões, Professor Auxiliar, msimoes@dei.uc.pt, http://apps.uc.pt/mypage/faculty/uc26855
Marco Vieira, Professor Catedrático, mvieira@dei.uc.pt, http://faculty.uc.pt/uc26592
Maria Marcelino, Professora Auxiliar, zemar@dei.uc.pt, http://apps.uc.pt/mypage/faculty/uc22660
Marília Curado, Professora Catedrática, marilia@dei.uc.pt, https://apps.uc.pt/mypage/faculty/marilia
Mário Rela, Professor Auxiliar, mzrela@dei.uc.pt, http://faculty.uc.pt/uc24500
Naghmeh Ivaki, Professora Auxiliar, naghmeh@dei.uc.pt, https://www.cisuc.uc.pt/en/people/naghmeh-ivaki
Nuno Laranjeiro, Professor Associado c/ Agregação, cnl@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc26646
Nuno Lourenço, Professor Associado, naml@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc26856/en
Paula Alexandra Silva, Professora Auxiliar, paulasilva@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc45348
Paulo Rupino, Professor Associado c/ Agregação, rupino@dei.uc.pt, http://faculty.uc.pt/uc25527
Paulo Simões, Professor Associado, psimoes@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc25711/en
Paulo de Carvalho, Professor Catedrático, carvalho@dei.uc.pt, https://www.cisuc.uc.pt/en/people/paulo-carvalho
Pedro Abreu, Professor Associado c/ Agregação, pha@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc40768/pt
Pedro Furtado, Professor Auxiliar, pnf@dei.uc.pt, https://www.cisuc.uc.pt/en/people/pedro-furtado
Pedro Martins, Professor Associado, pjmm@dei.uc.pt, https://www.cisuc.uc.pt/en/people/pedro-martins
Penousal Machado, Professor Associado c/ Agregação, machado@dei.uc.pt, http://faculty.uc.pt/uc26593
Raul Barbosa, Professor Auxiliar, rbarbosa@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc26844
Rui Pedro Paiva, Professor Associado c/ Agregação, ruipedro@dei.uc.pt, https://apps.uc.pt/mypage/faculty/uc26118
Teresa Mendes, Professora Catedrática Jubilada, tmendes@dei.uc.pt, https://www.cisuc.uc.pt/en/people/teresa-mendes
Tiago Cruz, Professor Associado c/ Agregação, tjcruz@dei.uc.pt, http://faculty.uc.pt/uc41531
Tiago Martins, Professor Auxiliar, tiagofm@dei.uc.pt, https://www.cisuc.uc.pt/en/people/tiago-martins
Vasco Pereira, Professor Auxiliar, vasco@dei.uc.pt, http://faculty.uc.pt/uc26416
"""

# Clean and split into lines
lines = [line.strip() for line in raw_data.strip().split('\n') if line.strip()]
reader = csv.reader(lines)

# Skip header
next(reader)

# Build and print the formatted output
#for row in reader:
#    if len(row) != 4:
#        continue  # skip malformed lines
#    nome, categoria, email, perfil = map(str.strip, row)
#    print(f"O Professor {nome} está na categoria {categoria}")

#for row in reader:
#    if len(row) != 4:
#        continue  # skip malformed lines
#    nome, categoria, email, perfil = map(str.strip, row)
#    print(f"O Professor {nome} pode ser contactado através do email {email}") 

for row in reader:
    if len(row) != 4:
        continue  # skip malformed lines
    nome, categoria, email, perfil = map(str.strip, row)

    print(f"# Professor {nome}:\n")
    print(f"nome: {nome}")
    print(f"categoria: {categoria}")
    print(f"email: {email}")
    print(f"perfil: {perfil}\n")

lines = [line.strip() for line in raw_data.strip().split('\n') if line.strip()]
reader = csv.reader(lines)

# Skip header
next(reader)

categorias = []
total_professores = 0

for row in reader:
    if len(row) != 4:
        continue
    nome, categoria, email, perfil = map(str.strip, row)
    categorias.append(categoria)
    total_professores += 1

categoria_counts = Counter(categorias)

# Output
print(f"Total de professores: {total_professores}")
print(f"Número de categorias distintas: {len(categoria_counts)}\n")
print("Número de professores por categoria:")
for cat, count in categoria_counts.items():
    print(f"  {cat}: {count}")
