class doc:
    def __init__(self, title, text):
        self.title = title
        self.text = text

    def count(self):
        res = len(self.text)
        return res

    def minicount(self):
        minires = self.text[:30] + '...'
        return minires
    
doc1 = doc("doc1.txt", "Вільям Уоллес - знакова, дуже важлива фігура в історії Шотландії. Він був вождем боротьби шотландців за свою свободу та звільнення від британського панування в часи короля Едуарда, названого Довгоногим ...")
doc2 = doc("doc2.txt", "А Вільям Уоллес втратив жінку, яку любив усією душею ... Тоді він почав свою війну проти свавілля англійців ...")

document = [doc1, doc2]

for i in document:
    print("Файл: ", i.title, "кількість символів: ", i.count(), "перші 30 символів: ", i.minicount())
    print("--------------------")
    
