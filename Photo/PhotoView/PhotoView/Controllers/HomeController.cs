﻿using System;
using System.IO;
using System.Web.Mvc;

namespace PhotoView.Controllers
{
	public class HomeController : Controller
	{
		public ActionResult Index()
		{
			return View();
		}

		public ActionResult About()
		{
			ViewBag.Message = "Your application description page.";

			return View();
		}

		public ActionResult Test2()
		{
			ViewBag.Message = "Your contact page.";

			return View();
		}
    }
}