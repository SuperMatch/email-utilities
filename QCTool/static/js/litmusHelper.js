var linker = angular.module('Linker', []).config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');
});


linker.factory('Data', function () {
    var Data = {}
    Data.warningDisplay = "show";
    Data.listDisplay = "hidden";
    Data.litmusURL = "";
    Data.config = [
        {
            name: "Apple Mail 6",
            suffix: "appmail6"
        },
        {
            name: "Lotus Notes 6.5",
            suffix: "notes6"
        },
        {
            name: "Lotus Notes 7",
            suffix: "notes7"
        },
        {
            name: "Lotus Notes 8",
            suffix: "notes8"
        },
        {
            name: "Lotus Notes 8.5",
            suffix: "notes85"
        },
        {
            name: "Outlook 2000",
            suffix: "ol2000"
        },
        {
            name: "Outlook 2002",
            suffix: "ol2002"
        },
        {
            name: "Outlook 2003",
            suffix: "ol2003"
        },
        {
            name: "Outlook 2007",
            suffix: "ol2007"
        },
        {
            name: "Outlook 2010",
            suffix: "ol2010"
        },
        {
            name: "Outlook 2011",
            suffix: "ol2011"
        },
        {
            name: "Outlook 2013",
            suffix: "ol2013"
        },
        {
            name: "Thunderbird latest",
            suffix: "thunderbirdlatest"
        },
        {
            name: "Android 2.3",
            suffix: "android22"
        },
        {
            name: "Android 4.2",
            suffix: "android4"
        },
        {
            name: "Gmail App (Android)",
            suffix: "androidgmailapp"
        },
        {
            name: "Black Berry 4 OS",
            suffix: "blackberry8900"
        },
        {
            name: "Black Berry 5 OS",
            suffix: "blackberryhtml"
        },
        {
            name: "iPhone 5s",
            suffix: "iphone5s"
        },
        {
            name: "iPad (Retina)",
            suffix: "ipad"
        },
        {
            name: "iPad Mini",
            suffix: "ipadmini"
        },
        {
            name: "iPhone 4s",
            suffix: "iphone4"
        },
        {
            name: "iPhone 5",
            suffix: "iphone5"
        },
        {
            name: "iPhone 6",
            suffix: "iphone6"
        },
        {
            name: "iPhone 6 Plus",
            suffix: "iphone6plus"
        },
        {
            name: "Windows Phone 8",
            suffix: "windowsphone8"
        },
        {
            name: "AOL Mail (Explorer)",
            suffix: "aolonline"
        },
        {
            name: "AOL Mail (Firefox)",
            suffix: "ffaolonline"
        },
        {
            name: "AOL Mail (Chrome)",
            suffix: "chromeaolonline"
        },
        {
            name: "Gmail (Explorer)",
            suffix: "gmailnew"
        },
        {
            name: "Gmail (Firefox)",
            suffix: "ffgmailnew"
        },
        {
            name: "Gmail (Chrome)",
            suffix: "chromegmailnew"
        },
        {
            name: "Outlook.com (Explorer)",
            suffix: "outlookcom"
        },
        {
            name: "Outlook.com (Firefox)",
            suffix: "ffoutlookcom"
        },
        {
            name: "Outlook.com (Chrome)",
            suffix: "chromeoutlookcom"
        },
        {
            name: "Yahoo! Mail (Explorer)",
            suffix: "yahoo"
        },
        {
            name: "Yahoo! Mail (Firefox)",
            suffix: "ffyahoo"
        },
        {
            name: "Yahoo! Mail (Chrome)",
            suffix: "chromeyahoo"
        }
    ];
    return Data;
});


function renderLink($scope, Data){
    $scope.data = Data;
    $scope.config = Data.config;
    $scope.renderLink = function (device) {
        var renderURL = Data.stripURL + "results#";
        return baseUrl = renderURL + device.suffix + "-full_on";
    }
}

function linkInput($scope, Data){
    $scope.data = Data;
    $scope.change = function () {
        var regex = /(https:\/\/litmus.com\/tests\/\d+\/versions\/\d+\/).*/
        var result = Data.litmusURL.match(regex);
        if(result){
            Data.stripURL = result[1]
            Data.warningDisplay = "hidden";
            Data.listDisplay = "show";
        }else{
            Data.stripURL = ""
            Data.warningDisplay = "show";
            Data.listDisplay = "hidden";
        }
    }
}