var AutoSuggestApp = {};
AutoSuggestApp.autoSuggester = function(){

    var substringMatcher = function(strs) {
        return function findMatches(q , cb ) {
            var matches, substringRegex;
            matches = [];
            substrRegex = new RegExp(q, 'i');

            $.each(strs, function(i, str) {
                if (substrRegex.test(str['name'])) {
                    matches.push(str);
                }
            });

            cb(matches);
        };
    };


    var busyItemsMatcher = function(itemNames) {
        return function findMatches(q , cb ) {
            var matches, substringRegex;
            matches = [];
            substrRegex = new RegExp('^'+q+'','i');

            var matchedIndex = 0;
            for(var i=0;i<itemNames.length;i++){
                if(substrRegex.test(itemNames[i]["name"])){
                    matchedIndex = i;
                    break;
                }
            }
            if(itemNames[matchedIndex]["name"].toLowerCase() == q){
                matches =itemNames.slice(matchedIndex,matchedIndex+1);
            }else{
                matches =itemNames.slice(matchedIndex,matchedIndex+100);
            }

            cb(matches);
        };
    };

    var getSuggest = function(sourceData,parentCont,placeholder,searchCont,callBack,searchFunc,template){


        template = template || "<%= name %>";
        searchFunc = searchFunc || "busy";
        callBack = callBack || function(item){ console.log(item); };
        $('#'+parentCont).html("<input id='"+ searchCont +"' size=50 type='search' class='form-control' placeholder='"+placeholder+"' size=50 />");
        $('#'+searchCont).typeahead({highlight:true}, {
            displayKey: 'num',
            limit : 100,
            //source: AutoSuggestApp.autoSuggester.substringMatcher(sourceData,callBack,parentCont) ,
            source: searchFunc=="busy" ? AutoSuggestApp.autoSuggester.busyItemsMatcher(sourceData,callBack,parentCont) :AutoSuggestApp.autoSuggester.substringMatcher(sourceData,callBack,parentCont) ,
            templates:{ suggestion: _.template(template)}
        });

        $('#'+searchCont).on('typeahead:opened',function(){$('.tt-dropdown-menu').css('width',$('#'+searchCont).width()*2 + 'px');});

        $('#'+searchCont).bind('typeahead:selected', function(obj, datum, name) {
            callBack(datum,parentCont);
        });
    } ;

    return {
        substringMatcher : substringMatcher,
        getSuggest : getSuggest,
        busyItemsMatcher : busyItemsMatcher

    }

}();