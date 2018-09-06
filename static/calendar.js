let startDate = document.querySelector('.calStart');
let today = new Date(startDate.innerHTML);
let month = today.getMonth();

Date.prototype.getMonths = function() {
  return [ 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December' ];
}

Date.prototype.getDays = function() {
    return new Date( this.getFullYear(), this.getMonth() + 1, 0 ).getDate();
}

Date.prototype.calendar = function() {
    let numOfDays = this.getDays();
    let startDay = new Date(this.getFullYear(), this.getMonth(), 1).getDay();
    let thisYear = this.getFullYear();
    let thisMonth = this.getMonths()[this.getMonth()];
    // let calendarTable = '<table summary="Calendar" class="calendar" style="text-align: center;">';
    let calendarTable = document.createElement('table');
    calendarTable.className = 'calendar';
    // calendarTable += '<span class="calTitle">' + this.getMonths()[this.getMonth()] + '&nbsp;' + this.getFullYear() + '</span>';
    let calSpan = document.createElement('span')
    calSpan.className = 'calTitle';
    calSpan.textContent = thisMonth + '  ' + thisYear;
    calendarTable.appendChild(calSpan);
    // calendarTable += '<tr><td colspan="7"></td></tr>';
    // let rows = document.createElement('tr');
    // let d = document.createElement('td');
    // d.colspan = '7';
    // rows.appendChild(d);
    // calendarTable.appendChild(rows);
    let calDayRow = document.createElement('tr');
    calDayRow.className = 'dayRow'

    // calendarTable += '<tr class="dayRow">';
    let calSun = document.createElement('td');
    calSun.textContent = 'SUN';
    calDayRow.appendChild(calSun)
    let calMon = document.createElement('td');
    calMon.textContent = 'MON';
    calDayRow.appendChild(calMon)
    let calTues = document.createElement('td');
    calTues.textContent = 'TUES';
    calDayRow.appendChild(calTues);
    let calWed = document.createElement('td');
    calWed.textContent = 'WED';
    calDayRow.appendChild(calWed);
    let calThurs = document.createElement('td');
    calThurs.textContent = 'THURS';
    calDayRow.appendChild(calThurs);
    let calFri = document.createElement('td');
    calFri.textContent = 'FRI';
    calDayRow.appendChild(calFri);
    let calSat = document.createElement('td');
    calSat.textContent = 'SAT';
    calDayRow.appendChild(calSat);
    calendarTable.appendChild(calDayRow);
    // calendarTable += '<td>S</td>';
    // calendarTable += '<td>M</td>';
    // calendarTable += '<td>T</td>';
    // calendarTable += '<td>W</td>';
    // calendarTable += '<td>TH</td>';
    // calendarTable += '<td>F</td>';
    // calendarTable += '<td>S</td></tr>';
    // Blank days, before month begins
    let blank;
    let calendarRow;
    for ( var i = 0; i < startDay; i++ ) {
        // calendarTable += '<td>&nbsp;</td>';
        calendarRow = document.createElement('tr');
        blank = document.createElement('td');
        blank.textContent = '';
        blank.className = 'blankDay';
        // blank.textContent = '\xa0';
        calendarRow.appendChild(blank);
    }
    // Counter counts through days of week. Each new date must check modulo 7
    // == 0; if so start a new week.
    let counter = startDay;
    let calendarDay;
    for (i = 1; i <= numOfDays; i++) {
        calendarRow = document.createElement('tr');
        calendarDay = document.createElement('td');
        counter++;
        if (( month === this.getMonth()) && ( today.getDate() == i )) {
          calendarDay.textContent = i;
          calendarDay.className = 'calDay'
          let text = document.createTextNode('First day of trip!!');
          let div = document.createElement('div');
          div.appendChild(text);
          calendarDay.appendChild(div);
        }else {
          // calendarTable += '<td class="calDay">' + i + '</td>';
          calendarDay.textContent = i;
          calendarDay.className = 'calDay'
        }
        calendarRow.appendChild(calendarDay);
        if ((( counter % 7 ) === 0 ) && ( i < numOfDays )) {
            //Make new row
            // calendarTable += '</tr>';
            calendarTable.appendChild(calendarRow);
            // calendarRow.innerHTML = '';
        }
    }
    // once iterated through all days in month(numOfDays) pad the rest of
    // the days in the week with blank days
    while(( counter++ % 7)!= 0) {
        // calendarTable += '<td>&nbsp;</td>';
        let blankTwo = document.createElement('td');
        // blankTwo.textContent = '\xa0'
        blankTwo.textContent = '';
        blankTwo.className = 'blankDay';
        calendarRow.apendChild(blankTwo);
        calendarTable.appendChild(calendarRow);
      }
      // close table
    // calendarTable += '</table>';
    return calendarTable;
}

window.onload = function() {
    // selected_month = '<form name="month_holder">';
    let selected_month = document.createElement('form');
    let selector = document.createElement('select');
    selector.id = 'month_items';
    selector.size = '1'
    selector.setAttribute('onchange', function(){month_picker()});
    let monthSel = document.createElement('option');
    // selected_month += '<select id="month_items" size="1" onchange="month_picker();">';
    for ( var x = 0; x <= today.getMonths().length; x++ ) {
        // selected_month += '<option value="' + today.getMonths()[x] + ' 1, ' + today.getFullYear() + '">' + today.getMonths()[x] + '</option>';
        monthSel.value = today.getMonths()[x] + today.getFullYear();
        monthSel.textContent = today.getMonths()[x];
        selector.appendChild(monthSel);
        // monthSel.innerHTML = '';
    }
    // End selector and form
    // selected_month += '</select></form>';
    selected_month.appendChild(selector);
    let actual_calendar = document.getElementById('show_calendar');
    actual_calendar.appendChild(today.calendar());
    let month_listing = document.getElementById('current_month');
    month_listing.appendChild(selected_month);
    actual_month = document.getElementById('month_items');
    actual_month.selectedIndex = month;
}
function month_picker(){
    month_menu = new Date(actual_month.value);
    actual_calendar.innerHTML = month_menu.calendar();
}
