// This is a bunch of ad-hoc fixes to make our Proposals form
// work the way we want. Mostly datagridfield.

function updateSelectOptions(select, options) {
  const nopt = select.options.length;
  // Save currently selected in case it exists in new list
  const currSel = select.value;
  //console.log("Current: "+currSel);
  for (let i = nopt-1 ; i >= 0 ; i--){
    select.remove(i);
  }
  for (let i = 0 ; i < options.length ; i++) {
    select.options.add(new Option(options[i][0],options[i][1]));
    //console.log("Adding option ",options[i][0]);
    if (options[i][1] == currSel) {
      //console.log("set value");
      select.value = options[i][1];
    }
  }
}

function updateNumProjects() {
  // When the number of projects changes, update the vocabularies
  // to be consistent
  const projrows = $('#form-widgets-projects tbody tr:not([data-index="TT"])');
  const runsrows = $('#form-widgets-runs tbody tr:not([data-index="TT"])');
  const Nproj = projrows.length;
  if (Nproj < 1) Nproj = 1;  // deal with first loading of page
  var newList = []
  // The new vocabulary
  for (let i = 0 ; i < Nproj ; i++) {
    newList.push([String(i+1),String(i+1)]);
  }
  projrows.each(function(index){
    $(this).find('span:first-child').text(String(index+1));
    //console.log("index:",index+1);
    updateSelectOptions($(this).find('select').get(0), newList);
  });
  runsrows.each(function() {
    updateSelectOptions($(this).find('select').get(0), newList);
  });
}

// First off, get rid of the in-line validation. This requires
// removing the "pat-validation" class everywhere.
$('.pat-validation').removeClass('pat-validation');

// Get rid of the stupid "No value" and put in -- instead.
$(function() {
   $('select option:contains("No value")').text("--");
});
/* Datagridfield handlers. This function code will be called
   whenever a new row is added to a datagridfield widget. It
   handles:
    1) Setting proper options for the project priorities.
    2) Adding a handler for selecting telescopes that properly
       sets the options for instruments.  
*/
let handleDGFInsert = function(event, dgf, row) {
   handleDGFRow(row);
}

let updateTelescopeInstruments = function(row) {
  //console.log("updateTelescopeInstruments:",row);
  const allinst = document.getElementById('form-widgets-runs-TT-widgets-inst1');
  const telescope = $(row).find('select:eq(5)').val();
  //console.log("telescope:",telescope);
  let newInstList = [["--","--NOVALUE--"]];
  if (telescope != "--NOVALUE--") {
    $(row).find('select:eq(6)').prop("disabled", false);
    if (telescope == "Swope") {
      $(row).find('select:eq(7)').prop("disabled", true);
    } else {
      $(row).find('select:eq(7)').prop("disabled", false);
    }
    // Build list of instruments
    for (let j = 0 ; j < allinst.options.length; j++) {
      if (allinst.options[j].value.includes(telescope)) {
        let arr = allinst.options[j].value.split(":");
        let N = arr.length;
        let newstr = arr.slice(1,N).join(":").trim();
        newInstList.push([newstr, allinst.options[j].value]);
      }
    }
  }
  const selects = row.querySelectorAll('.select-widget');
  for (let i = 0 ; i < selects.length ; i++) {
    if (selects[i].name.includes('TT')) continue;
    if (selects[i].name.includes('widgets.inst1') || selects[i].name.includes('widgets.inst2')) {
      //console.log('newinstlist:',newInstList)
      updateSelectOptions(selects[i], newInstList);
    }
  }
}

let handleDGFRow = function(row) {
  //console.log("handleDGRRow",row);
  row = $(row);
  let parent = row.closest('table');
  const widgetName = parent[0].id;
  parent = parent.children('tbody');
  if (widgetName == "form-widgets-projects") {
    const elems = parent.find("select");
    const Nproj = parent[0].rows.length - 1;
    updateNumProjects();

    // Newly added row should have Nproj as the project number
    parent.find(".select-widget:last").val(String(Nproj));

    let delbut = row.find(".dgf--row-delete").get(0)
    delbut.addEventListener("click", function(e) {
       updateNumProjects();
    });
  }
  if (widgetName == "form-widgets-runs") {
    // Project listing should only include number of projects
    const projrows = $("#form-widgets-projects tbody tr");
    let Nproj = projrows.length - 1;
    if (Nproj < 1) Nproj = 1; // handle first loading of form
    let newList = [];
    for (let j = 0 ; j < Nproj; j++) {
      newList.push([String(j+1),String(j+1)]);
    }
    const projsel = row.find('select').get(0);
    updateSelectOptions(projsel, newList);

    updateTelescopeInstruments(row[0]);

    // Now handle telescope selection
    const select = row[0].querySelector('[name$="telescope:list"]');
    select.addEventListener('change', function(event) {
      const allinst = document.getElementById('form-widgets-runs-TT-widgets-inst1');
      const target = event.target;
      const telescope = target.value.trim();
      const row = target.parentElement.parentElement;
      updateTelescopeInstruments(row);
    });
  }
};

$(document).ready( function() {
  //updateNumProjects();
  $('tr.datagridwidget-row').each(function(index,element) {
    var $row=$(element);
    handleDGFRow($row);
  })
});
$(document).on('afteraddrow', '.pat-datagridfield', handleDGFInsert);