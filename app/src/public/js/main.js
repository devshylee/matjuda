const today = new Date().getDay(); // 오늘 요일 (0: 일요일, 1: 월요일, ...)
const weekdays = [
  "월요일",
  "화요일",
  "수요일",
  "목요일",
  "금요일",
  "토요일",
  "일요일",
];
const day = today === 0 ? "일요일" : weekdays[today - 1]; // 오늘 요일 문자열

// JSON 데이터 불러오기
const url = "./public/crawling/daelim_menu.json";

fetch(url)
  .then((response) => response.json())
  .then((data) => {
    const menus = data;

    // 각 식당 메뉴 출력
    const menuCorner1 = document.getElementById("menu-corner1");
    menuCorner1.innerHTML = menus.Corner1[day].join("<br />");

    const menuCorner3 = document.getElementById("menu-corner3");
    menuCorner3.innerHTML = menus.Corner3[day].join("<br />");

    const menuBreakfast = document.getElementById("menu-breakfast");
    menuBreakfast.innerHTML = menus.조식[day].join("<br />");

    const menuCorner6 = document.getElementById("menu-corner6");
    menuCorner6.innerHTML = menus.Corner6[day].join("<br />");

    const menuDaelimcook = document.getElementById("menu-daelimcook");

    if (menus.hasOwnProperty("Daelim Cook")) {
      menuDaelimcook.innerHTML = menus["Daelim Cook"][day].join("<br />");
    } else if (menus.hasOwnProperty("Daelimcook")) {
      menuDaelimcook.innerHTML = menus.Daelimcook[day].join("<br />");
    }
  });

document.getElementById("today-day").innerHTML = day;
