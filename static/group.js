//variables
// const groupNum = document.querySelector('#groupId').textContent;
// const expenseList = document.querySelector('.resultList');
// const totalExpense = document.querySelector('.totalResult');
// const grandTotal = document.querySelector('.grandTotal')
// const results = document.querySelector('.results');
// const res = document.querySelector('.resultList');
// const name = document.querySelector('.calcName');
// const price = document.querySelector('#calcPrice');
// const divisor = document.querySelector('#calcDivideBy');
// const type = document.querySelector('#calcSelect');
// const multiple = document.querySelector('#calcDays');
// const budgetForm = document.querySelector('.budgetForm');
// const budget = document.querySelector('.budget')
//
// //load event listeners
// function loadEventListeners() {
//   // document.querySelector('#calcSubmit').addEventListener('click', calculateResults);
//   // document.addEventListener('DOMContentLoaded', getExpenses);
//   document.querySelector('.expenseDelete').addEventListener('click', deleteExpenses);
//   document.querySelector('.resultList').addEventListener('click', deleteIndExp);
// }
//
// loadEventListeners();
//
// checkBudget();
//
// function checkBudget(){
//   if (budget === null) {
//     budgetForm.style.display = 'block';
//   }
// }
//
// function deleteExpenses(e) {
//   if (confirm('Are you sure you want to clear all Expenses?')) {
//     localStorage.clear();
//     while (expenseList.firstChild) {
//       expenseList.removeChild(expenseList.firstChild);
//     }
//     while (totalExpense.firstChild) {
//       totalExpense.removeChild(totalExpense.firstChild);
//     }
//   }
//   e.preventDefault();
// }
//
//
// function deleteIndExp(e) {
//     if (e.target.parentElement.classList.contains('calculatorResults')) {
//         if (confirm('Are you sure you want to clear this expense?')) {
//             let list = document.querySelectorAll('.calculatorResults');
//             let counter = 0;
//             for (i=0;i<list.length;i++) {
//                 if (e.target.parentElement === list[i]) {
//                     break;
//                 }
//                 counter += 1;
//             }
//             let counter2 = 0;
//             e.target.parentElement.remove();
//             let group = JSON.parse(localStorage.getItem('whichGroup'));
//             for (i=0;i<group.length;i++) {
//                 if (group[i] == groupNum) {
//                     if (counter === counter2) {
//                         let expos = JSON.parse(localStorage.getItem('expenses'));
//                         let typos = JSON.parse(localStorage.getItem('types'));
//                         let price = parseFloat(expos[i]);
//                         expos.splice(i, 1);
//                         typos.splice(i, 1);
//                         group.splice(i, 1);
//                         localStorage.setItem('expenses', JSON.stringify(expos));
//                         localStorage.setItem('types', JSON.stringify(typos));
//                         localStorage.setItem('whichGroup', JSON.stringify(group));
//                         let total = parseFloat(localStorage.getItem(groupNum));
//                         total = (total - price).toFixed(2);
//                         localStorage.setItem(groupNum, total);
//                         getTotal();
//                         break;
//                     }
//                     counter2 += 1;
//                 }
//
//             }
//         }
//     }
//     e.preventDefault();
// }
// function getExpenses() {
//   // const item = document.querySelector('#expenseResults');
//     if (localStorage.getItem('expenses') === null){
//         results.style.display = 'none'
//     } else {
//         results.style.display = 'block';
//         let expenseStorage = JSON.parse(localStorage.getItem('expenses'));
//         let typeStorage = JSON.parse(localStorage.getItem('types'));
//         let groups = JSON.parse(localStorage.getItem('whichGroup'));
//         for (i=0;i<expenseStorage.length;i++){
//             if (groups[i] === groupNum) {
//                 let li = document.createElement('li');
//                 li.className = 'calculatorResults';
//                 let textNode = document.createTextNode("$" + expenseStorage[i] + " " + typeStorage[i] + " expense.");
//                 li.appendChild(textNode);
//                 document.querySelector('.resultList').appendChild(li);
//                 let link = document.createElement('a');
//                 let xnode = document.createTextNode('Clear');
//                 link.appendChild(xnode);
//                 li.appendChild(link);
//                 link.className = 'deleteX';
//                 link.href = '#';
//             }
//         }
//     getTotal();
//     }
// }
// function showErrorMessage(message, type) {
//   let div = document.createElement('div');
//   div.className = (type);
//   div.classList += ' alert';
//   div.appendChild(document.createTextNode(message));
//   let container = document.querySelector('.calcDiv');
//   let form = document.querySelector('.expenseForm');
//   container.insertBefore(div, form);
//   setTimeout(function(){
//       document.querySelector('.alert').remove();
//   },5000);
// }
//
// function calculateResults(e){
//     if (price.value < 1 || divisor.value < 1 || multiple.value < 1 || type.value === '') {
//         showErrorMessage('Please fill out all form values.', 'error');
//         e.preventDefault();
//
//     }else {
//       let expense = price.value * multiple.value / divisor.value;
//       document.querySelector('.results').style.display = 'block';
//       //Create the title and result element
//       // let title = document.createElement('h5');
//       let li = document.createElement('li');
//       // title.className = 'nameExpense';
//       li.className = 'calculatorResults';
//       // let nameNode = document.createTextNode(name.value);
//       let node = document.createTextNode("$" + expense.toFixed(2) + " " + type.value + " expense.");
//       // title.appendChild(nameNode);
//       li.appendChild(node);
//       // res.appendChild(title);
//       res.appendChild(li);
//       //Create delete X
//       let link = document.createElement('a');
//       let xnode = document.createTextNode('Clear');
//       link.appendChild(xnode);
//       li.appendChild(link);
//       link.className = 'deleteX';
//       link.href = '#';
//       price.value = '';
//       divisor.value = '';
//       multiple.value = '';
//       // name.value = ''
//       let total;
//       if (localStorage.getItem(groupNum) === null) {
//           total = 0;
//        }else {
//           total = JSON.parse(localStorage.getItem(groupNum));
//       }
//       total += expense;
//       localStorage.setItem(groupNum, total.toFixed(2));
//       storeExpenseInLocalStorage(expense, type.value);
//       getTotal();
//       showErrorMessage('Expense added!', 'success');
//       e.preventDefault();
//     }
// }
//
//
// function getTotal() {
//   document.querySelector('.totalResult').style.display = 'block';
//   let totalDiv = document.createElement('div');
//   if (document.querySelector('.grandTotal') != null) {
//     document.querySelector('.grandTotal').remove();
//   }
//   totalDiv.className = 'grandTotal';
//   let node = document.createTextNode("$" + localStorage.getItem(groupNum));
//   totalDiv.appendChild(node);
//   document.querySelector('.totalResult').appendChild(totalDiv);
// }
//
// function storeExpenseInLocalStorage(cost, type2) {
//   let expenses;
//   let types;
//   let groups;
//   // let names;
//   if (localStorage.getItem('expenses') === null) {
//     expenses = [];
//     types = [];
//     groups = [];
//     // names = [];
//   }else {
//     expenses = JSON.parse(localStorage.getItem('expenses'));
//     types = JSON.parse(localStorage.getItem('types'));
//     groups = JSON.parse(localStorage.getItem('whichGroup'));
//     // names = JSON.parse(localStorage.getItem('names'));
//   }
//   expenses.push(cost.toFixed(2));
//   types.push(type2);
//   groups.push(groupNum);
//   // names.push(title);
//   localStorage.setItem('expenses', JSON.stringify(expenses));
//   localStorage.setItem('types', JSON.stringify(types));
//   localStorage.setItem('whichGroup', JSON.stringify(groups));
//   // localStorage.setItem('names', title);
// }
//
// if (document.querySelector('.formErrorPin') != null) {
//     let errors = document.querySelectorAll('.formErrorPin');
//     errors.forEach(function(error) {
//         setTimeout(function(){
//             error.remove();
//         },5000)
//     })
// }
