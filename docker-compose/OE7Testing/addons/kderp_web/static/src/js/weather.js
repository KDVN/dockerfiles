$(document).ready(function (){
    ////getting current weather
    function displayWeather(lat, lon, timeout) {
        //var weatherAPI = "http://api.wunderground.com/api/4844c2f37dbc3540/conditions/lang:VU/q/" + lat + "," + lon + ".json";
        var weatherAPI = "http://thcn-api.herokuapp.com/api/weathers/now/"  + lat + "," + lon;
        $.getJSON(weatherAPI, function (data) {
            var conditions = data.current_observation;
            if (conditions != undefined && conditions.temp_c != undefined)
                var temp = conditions.temp_c;
            else
                var temp = 'N/A';
            var feellike = conditions.feelslike_c;
            var city = conditions.display_location.city;
            var desc = conditions.weather;
            html = "<div id='weather' class='weatherFeed'>" +
                        "<img class='weatherItem' src='" + conditions.icon_url + "'>" +
                        "<div class='weatherCity text-right pull-right'>" + city + "(1" +  desc + ")</div>" +
                        "<div class='weatherTemp'>" + feellike + "&#8451;</div>" +
                    "</div>";
            setTimeout(function() {
                $("#weather").html(html);
            },timeout);
        });
    }

    //get current location or city
    //using http://ip-api.com/json
    //
    function showWeather() {
        var locAPI = "http://ip-api.com/json";
        $.getJSON(locAPI, function (data) {
            city = data.city;
            lat = data.lat;
            lon = data.lon;
            //updating city name
            //$("#location").text(city);
            //get current weather
            displayWeather(lat, lon, 500);
            setInterval(function (){displayWeather(lat, lon, 0)}, 7200000);
        });
    };
    showWeather();
});
